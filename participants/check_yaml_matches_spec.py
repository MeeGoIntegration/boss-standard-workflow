#!/usr/bin/python --tt
"""Check the yaml and spec file coherence in submit request.

The check does the following for each package:

  #. If spec file is present and claims to be generated by spectacle, make sure
     that also yaml file is present.
  #. If yaml file is present, make sure that executing specify does not change
     the spec file

:term:`Workitem` fields IN:

:Parameters:
    :ev.actions:
        List of OBS submit request actions describing the projects,
        packages, and revisions to look into.
    :ev.namespace:
        OBS alias definig the API URL to use


:term:`Workitem` fields OUT:

:Returns:
    result(Boolean):
        False if check failed

Check respects the values in [checks] section of packages boss.conf
for following keys:

    check_yaml_matches_spec:
        skip/warn this check

"""

import difflib, os, re, shutil, subprocess, tempfile
from buildservice import BuildService
from boss.checks import CheckActionProcessor

DEFAULT_SPEC_PATTERN = "Generated by: spectacle"

class Lab(object):
    """Controlled temporary directory with snapshot support.

    Can be used with 'with' statement to create disposable file storage.
    Does not support subdirectories.
    """
    def __init__(self):
        self.path = tempfile.mkdtemp(prefix="check_yaml_spec_")
        self._history = [self.path]

    def take_snapshot(self):
        """Take snapshot of the lab directory.

        :returns: Snapshot ID
        """
        index = len(self._history) - 1
        path = self.path + "_%d" % index
        self._history.insert(-1, path)
        shutil.copytree(self.path, path)
        return index

    def store(self, name, content):
        """Saves a file in the lab.

        :param name: File name
        :param content: File content
        """
        path = os.path.join(self.path, name)
        open(path, "w").writelines(content)

    def get_diff(self, name, from_sid, to_sid=None):
        """Compares the original file content between two snapshots

        :param name: File name
        :param from_sid: Snapshot ID to compare from
        :param to_sid: Snapshot id to compare to, uses current state if None
        :returns: List of changed lines
        """
        try:
            from_path = os.path.join(self._history[from_sid], name)
        except IndexError:
            raise ValueError("Bad from snapshot id %d" % from_sid)

        if to_sid is None:
            to_sid = -1
        try:
            to_path = os.path.join(self._history[to_sid], name)
        except IndexError:
            raise ValueError("Bad to snapshot id %d" % to_sid)
        if os.path.exists(from_path):
            from_lines = open(from_path).readlines()
        else:
            from_lines = []
        if os.path.exists(to_path):
            to_lines = open(to_path).readlines()
        else:
            to_lines = []
        diff = difflib.Differ().compare(from_lines, to_lines)
        return [line for line in diff if not line.startswith("  ")]

    def get_path(self, name, sid=None):
        """Get file path.

        :param name: File name
        :param sid: Snapshot id, use current if None
        :returns: Full path to file
        """
        if sid is None:
            sid = -1
        try:
            path = self._history[sid]
        except IndexError:
            raise ValueError("Bad snapshot id %d" % sid)
        return os.path.join(path, name)

    def cleanup(self):
        """Cleanup the lab and snapshots."""
        for path in list(self._history):
            shutil.rmtree(path)
            self._history.remove(path)
        self.path = None

    def __enter__(self):
        """Managed context entry point."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Managed context exit point."""
        self.cleanup()

class ParticipantHandler(object):
    """Participant class as defined by the SkyNET API."""

    def __init__(self):
        self.oscrc = None
        self.namespace = None
        self.obs = None
        self.spec_re = None

    def handle_lifecycle_control(self, ctrl):
        """Participant life cycle control."""
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")
            else:
                raise RuntimeError("Participant config missing "
                        "[obs] oscrc option")
            if ctrl.config.has_option("check_yaml", "spec_pattern"):
                pat = ctrl.config.get("check_yaml", "spec_pattern")
            else:
                pat = DEFAULT_SPEC_PATTERN
            self.spec_re = re.compile(pat)
            print "oscrc: %s" % self.oscrc
            print "spec_pattern: %s" % pat

    def handle_wi_control(self, ctrl):
        """Job control."""
        pass

    def setup_obs(self, namespace):
        """Set up OBS instance."""
        if not self.obs or self.namespace != namespace:
            self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)
            self.namespace = namespace

    def handle_wi(self, wid):
        """Job thread."""
        wid.result = False
        if not isinstance(wid.fields.msg, list):
            wid.fields.msg = []

        if not wid.fields.ev:
            raise RuntimeError("Missing mandatory field 'ev'")
        if not isinstance(wid.fields.ev.actions, list):
            raise RuntimeError("Mandatory field ev.actions not a list")
        if not isinstance(wid.fields.ev.namespace, basestring):
            raise RuntimeError("Mandatory field ev.namespace not a string")

        self.setup_obs(wid.fields.ev.namespace)

        result = True
        for action in wid.fields.ev.actions:
            pkg_result, _ = self.__handle_action(action, wid)
            result = result and pkg_result
        wid.result = result

    @CheckActionProcessor("check_yaml_matches_spec")
    def __handle_action(self, action, wid):
        """Process single action from OBS event info.

        :param wid: Workitem
        :param action: Single dictionary from OBS event actions list
        :returns: True if all good, False otherwise
        """
        project = action["sourceproject"]
        package = action["sourcepackage"]
        revision = action["sourcerevision"]
        files = self.obs.getPackageFileList(project, package, revision)

        with Lab() as lab:
            spec = None
            yaml = None
            for name in files:
                if name.endswith(".spec"):
                    lab.store(name, self.obs.getFile(project, package, name,
                        revision))
                    spec = name
                elif name.endswith(".yaml"):
                    lab.store(name, self.obs.getFile(project, package, name,
                        revision))
                    yaml = name

            if not (spec and
                    self.spec_re.search(open(lab.get_path(spec)).read())):
                # No spec file or spec not from spectacle, skip
                return True, None
            if not yaml:
                return False, "SPEC file generated with spectacle, " \
                              "but yaml not present"

            snapshot = lab.take_snapshot()
            # Download rest of the files
            files.remove(spec)
            files.remove(yaml)
            for name in files:
                lab.store(name, self.obs.getFile(project, package, name,
                        revision))

            # Run specify
            specify = subprocess.Popen(["specify", "-n", "-N",
                lab.get_path(yaml)], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, env={"ANSI_COLORS_DISABLED":"1"})
            rcode = specify.wait()
            if rcode != 0:
                return False, "Running specify failed:\n%s" \
                        % specify.stdout.read()
            # Get the diff
            diff = lab.get_diff(spec, snapshot)
            clean_diff = []
            for line in diff:
                # ignore the ? seperator lines
                if line[0] == "?":
                    continue
                # Remove diff markers and white space
                stripped = line[2:].strip()
                # skip empty lines
                if not stripped:
                    continue
                # skip comments
                if stripped[0] == "#":
                    continue
                # effective change
                clean_diff.append(line)
            if clean_diff:
                return False, "Spec file changed by specify:\n%s" \
                        % "".join(clean_diff)
        return True, None

