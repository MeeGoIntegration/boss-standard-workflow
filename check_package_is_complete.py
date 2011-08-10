#!/usr/bin/python
""" Makes sure that the packages being submitted contain the mandatory files: 
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

"""


from buildservice import BuildService

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

    def is_complete(self, prj, pkg, revision):

        """ Package file completeness check """

        filelist = self.obs.getPackageFileList(prj, pkg, revision)
        specfile = changesfile = sourcefile = False
        for fil in filelist:
            if fil.endswith(".tar.bz2") \
            or fil.endswith(".tar.gz") \
            or fil.endswith(".tgz"):
                sourcefile = True

            if fil.endswith(".changes"):
                changesfile = True

            if fil.endswith(".spec"):
                specfile = True

        return sourcefile and changesfile and specfile

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
            # Assert needed files are there.
            if not self.is_complete(action['sourceproject'],
                                    action['sourcepackage'],
                                    action['sourcerevision']):
                result = False
                wid.fields.msg.append("Package %s in project %s missing files."\
                                      "At least compressed source tarball, "\
                                      ".spec and .changes files should be "\
                                      "present" % (action['sourcepackage'],
                                                   action['sourceproject']))

        wid.result = result

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.setup_obs(wid.fields.ev.namespace)
        self.quality_check(wid)
