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


from buildservice import BuildService
from boss.checks import CheckActionProcessor

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

        specfile, _ = self.has_spec_file(action, wid, filelist)
        changesfile, _ = self.has_changes_file(action, wid, filelist)
        sourcefile, _ = self.has_source_file(action, wid, filelist)

        result = (sourcefile and changesfile and specfile)

        return result, msg
    
    @CheckActionProcessor("check_package_is_complete_tarball")
    def has_source_file(self, _action, _wid, filelist):
        """Check that filelist contains source tarball."""
        for name in filelist:
            if name.endswith(".tar.bz2") \
                    or name.endswith(".tar.gz") \
                    or name.endswith(".tgz"):
                return True, None
        return False, "No source tarball found"
    
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
            wid.fields.__error__ = "Mandatory field: actions does not exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field")

        self.setup_obs(wid.fields.ev.namespace)

        result = True
        for action in actions:
            # Assert needed files are there.
            pkg_complete, _ = self.is_complete(action, wid)
            if not pkg_complete:
                result = False
        wid.result = result
