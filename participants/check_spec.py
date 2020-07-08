#!/usr/bin/python3
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


    def handle_wi(self, wid):
        """ actual job thread """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        actions = wid.fields.ev.actions

        if not actions:
            raise RuntimeError("Mandatory field: actions does not exist.")

        self.setup_obs(wid.fields.ev.namespace)
        result = True

        for action in actions:
            # Assert validity of spec file
            valid, _ = self.spec_valid(action, wid)
            result = result and valid

        wid.result = result
