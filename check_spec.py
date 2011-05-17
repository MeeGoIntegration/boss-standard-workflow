#!/usr/bin/python
""" Quality check participant """

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


def hasSectionOrTag(spec, tag):
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
    
    def getSpecFile(self, prj, pkg, rev=None):

        """ Get a package's spec file """

        spec = ""
        file_list = self.obs.getPackageFileList(prj, pkg, revision=rev)
        for fil in file_list:
            if fil.endswith(".spec"):
                spec = self.obs.getFile(prj, pkg, fil)
        return spec

    def specValid(self, prj, pkg, revision):
        """
          Get spec file and check for various indications of spec file validity
        """
        result = True
        msg = []
        spec = self.getSpecFile(prj, pkg, revision)

        if hasSectionOrTag(spec, "%changelog"):
            result = False
            msg.append("Spec file for package %s should not contain the \
                        %%changelog tag, otherwise the changes file is \
                        ignored" % pkg)
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
            # Assert validity of spec file
            valid , msg = self.specValid(action['sourceproject'],
                                         action['sourcepackage'],
                                         action['sourcerevision'])
            if not valid:
                wid.fields.msg.extend(msg)
                result = False

        wid.result = result

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.setup_obs(wid.namespace)
        self.quality_check(wid)
