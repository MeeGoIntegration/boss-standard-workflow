#!/usr/bin/python
""" Implements a simple spec file validator according to the common guidlines :
   * Does not have a %changelog section

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if the spec files of all packages are valid, False otherwise.


Check respects the values in [checks] section of packages boss.conf
for following keys:

    check_spec:
        skip/warn this check

"""

from boss.checks import CheckActionProcessor
from boss.obs import BuildServiceParticipant


def has_section_or_tag(spec, tag):
    """ simple check function that is faster than the one above
        and doesn't use temporary files """
    return tag in spec


class ParticipantHandler(BuildServiceParticipant):

    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass

    def get_spec_file(self, prj, pkg, rev=None):

        """ Get a package's spec file """

        spec = ""
        file_list = self.obs.getPackageFileList(prj, pkg, revision=rev)
        for fil in file_list:
            if fil.endswith(".spec"):
                spec = self.obs.getFile(prj, pkg, fil, revision=rev)
        return spec

    @CheckActionProcessor("check_spec")
    def spec_valid(self, action, _wid):
        """
          Get spec file and check for various indications of spec file validity
        """
        spec = self.get_spec_file(action['sourceproject'],
                                  action['sourcepackage'],
                                  action['sourcerevision'])

        if has_section_or_tag(spec, "%changelog"):
            return False, "Spec file should not contain the %%changelog tag, "\
                    "otherwise the changes file is ignored."

        return True, None

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """ actual job thread """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        actions = wid.fields.ev.actions

        if not actions:
            raise RuntimeError("Mandatory field: actions does not exist.")

        result = True

        for action in actions:
            # Assert validity of spec file
            valid, _ = self.spec_valid(action, wid)
            result = result and valid

        wid.result = result
