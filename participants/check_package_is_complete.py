#!/usr/bin/python
"""
Makes sure that the packages being submitted contain the mandatory files:
   * compressed source file (tar.bz2, tar.gz, .tgz)
   * spec file
   * changes file

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if all packages are complete, False if a package was missing a file


Check respects the skip/warn values in [checks] section of packages boss.conf
for following keys:

    check_package_is_complete:
        skip/warn for all package completenes checks
    check_package_is_complete_tarball:
        skip/warn for missing source tarball file
    check_package_is_complete_changes:
        skip/warn for missing .changes file
    check_package_is_complete_spec:
        skip/warn for missing .spec file

"""

import os, rpm

from tempfile import NamedTemporaryFile
from buildservice import BuildService
from boss.checks import CheckActionProcessor

class SpecError(Exception):
    pass

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = None
        self.oscrc = None

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")

    def setup_obs(self, namespace):
        """ setup the Buildservice instance using the namespace as an alias
            to the apiurl """

        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    @CheckActionProcessor("check_package_is_complete")
    def is_complete(self, action, wid):
        """ Package file completeness check """

        filelist = self.obs.getPackageFileList(
                action['sourceproject'],
                action['sourcepackage'],
                action['sourcerevision'])

        spec = self.has_spec_file(action, wid, filelist)[0]
        changes = self.has_changes_file(action, wid, filelist)[0]
        sources = spec and self.check_source_files(action, wid, filelist)[0]

        return (spec and changes and sources), ""

    def get_spec_sources(self, action, filelist):
        """Extract source file list from package spec.

        :parma action: OBS request action dictionary
        :param filelist: List of package files
        :returns: List of source file names
        :raises SpecError: If something goes wrong
        """
        try:
            spec_name = [name for name in filelist if name.endswith(".spec")][0]
        except IndexError:
            raise SpecError("No spec file found.")
        try:
            spec = self.obs.getFile(action["sourceproject"],
                    action["sourcepackage"], spec_name,
                    action["sourcerevision"])
        except Exception, exobj:
            raise SpecError("Failed to fetch spec file %s/%s/%s rev %s: %s" % (
                    action["sourceproject"], action["sourcepackage"],
                    spec_name, action["sourcerevision"], exobj))
        try:
            tmp_spec = NamedTemporaryFile(mode="w")
            tmp_spec.file.write(spec)
            tmp_spec.file.flush()
            spec_obj = rpm.spec(tmp_spec.name)
            sources = [name for name, _, _ in spec_obj.sources]
            tmp_spec.close()
        except ValueError, exobj:
            raise SpecError("Failed to parse spec file: %s" % exobj)
        return sources

    @CheckActionProcessor("check_package_is_complete_sources")
    def check_source_files(self, action, _wid, filelist):
        """Check that filelist and spec sources match"""
        try:
            spec_sources = self.get_spec_sources(action, filelist)
        except SpecError, exobj:
            return False, str(exobj)
        extras = []
        for name in filelist:
            if os.path.splitext(name)[1] in (".spec", ".changes"):
                continue
            if name not in spec_sources:
                extras.append(name)
            else:
                spec_sources.remove(name)
        msg = ""
        if extras:
            msg += "Extra files in package: %s. " % ", ".join(extras)
        if spec_sources:
            msg += "Files listed in spec missing: %s" % ", ".join(spec_sources)
        if msg:
            return False, msg
        return True, None

    @CheckActionProcessor("check_package_is_complete_changes")
    def has_changes_file(self, _action, _wid, filelist):
        """Check that filelist contains `*.changes` file."""
        for name in filelist:
            if name.endswith(".changes"):
                return True, None
        return False, "No .changes file found"

    @CheckActionProcessor("check_package_is_complete_spec")
    def has_spec_file(self, _action, _wid, filelist):
        """Check that filelist contains `*.spec` file."""
        for name in filelist:
            if name.endswith(".spec"):
                return True, None
        return False, "No .spec file found"

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        wid.result = False
        actions = wid.fields.ev.actions

        if not actions:
            raise RuntimeError("Mandatory field ev.actions missing.")

        self.setup_obs(wid.fields.ev.namespace)

        result = True
        for action in actions:
            # Assert needed files are there.
            pkg_complete, _ = self.is_complete(action, wid)
            if not pkg_complete:
                result = False
        wid.result = result
