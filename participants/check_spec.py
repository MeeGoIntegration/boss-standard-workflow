#!/usr/bin/python
""" Implements a simple spec file validator according to the common guidlines :
   * Does not have a %changelog section
   * Current version is equal to the latest version in changelog

The prerequisites:
    * get_relevant_changelog

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`
   ev.actions[].relevant_changelog(string):
      content of .changes file

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if the spec files of all packages are valid, False otherwise.

"""

import re

from buildservice import BuildService

#def getSectionOrTag(spec, tag):
#    """
#      Reuse function from osc/core.py line 3055
#    """
#    try:
#        specfile = tempfile.NamedTemporaryFile(delete=False)
#        specfile.write(spec)
#        specfile.close()
#        d = read_meta_from_spec(specfile.name, tag)
#        return d[tag]
#    finally:
#        os.remove(specfile.name)


def has_section_or_tag(spec, tag):
    """ simple check function that is faster than the one above
        and doesn't use temporary files """
    return tag in spec

def is_version_updated(spec, changelog):
    """Check if spec's version is equal to the latest version in changelog."""

    def get_ver(pattern_str, string):
        """Look up for version in input string."""
        ver = None
        ver_pattern = re.compile(pattern_str)
        for line in string.splitlines():
            match = ver_pattern.match(line)
            if match:
                ver = match.group(1)
                break
        return ver

    spec_ver = get_ver(r"^Version:\s+(\d[\d\.]+)\s*$", spec)
    if not spec_ver:
        return False
    cl_ver = get_ver(r"\* .*<\w[\w\.]*@\w[\w\.]+> - (\d[\d\.]+)\s*$",
                     changelog)
    if not cl_ver:
        return False
    return spec_ver == cl_ver

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

    def get_spec_file(self, prj, pkg, rev=None):

        """ Get a package's spec file """

        spec = ""
        file_list = self.obs.getPackageFileList(prj, pkg, revision=rev)
        for fil in file_list:
            if fil.endswith(".spec"):
                spec = self.obs.getFile(prj, pkg, fil, revision=rev)
        return spec

    def spec_valid(self, prj, pkg, revision, changelog):
        """
          Get spec file and check for various indications of spec file validity
        """
        result = True
        msg = []
        spec = self.get_spec_file(prj, pkg, revision)

        if has_section_or_tag(spec, "%changelog"):
            result = False
            msg.append("Spec file for package %s should not contain the \
                        %%changelog tag, otherwise the changes file is \
                        ignored" % pkg)
        if not is_version_updated(spec, changelog):
            result = False
            msg.append("Version spec file for package %s should be the \
                        same as the latest version in changelog" % pkg)

        return result, msg

    def quality_check(self, wid):

        """ Quality check implementation """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        actions = wid.fields.ev.actions

        if not actions:
            wid.fields.__error__ = "Mandatory field: actions does not exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field")

        result = True

        for action in actions:
            changelog = action.get('relevant_changelog', None)
            if not changelog:
                wid.fields.__error__ = "Mandatory field: relevant_changelog does not exist."
                wid.fields.msg.append(wid.fields.__error__)
                raise RuntimeError("Missing mandatory field: relevant_changelog")

            # Assert validity of spec file
            valid , msg = self.spec_valid(action['sourceproject'],
                                         action['sourcepackage'],
                                         action['sourcerevision'],
                                         "\n".join(changelog))
            if not valid:
                wid.fields.msg.extend(msg)
                wid.fields.status = "FAILED"
                result = False

        wid.result = result

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.setup_obs(wid.fields.ev.namespace)
        self.quality_check(wid)
