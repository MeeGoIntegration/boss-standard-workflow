#!/usr/bin/python3
""" This participants gets the whole changelog of a certain package from the OBS
changes file cotained in it.

:term:`Workitem` fields IN:

:Parameters:
   project(string):
      Name of OBS project in which the package lives
   package(string):
      Name of OBS package in which the changelog lives

:term:`Workitem` fields OUT:

:Returns:
   changelog(string):
      The changelog fetched from OBS
   result(Boolean):
      True if everything was OK, False otherwise

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

    def get_changes_file(self, prj, pkg, rev=None):

        """ Get a package's changes file """

        changelog = ""
        file_list = self.obs.getPackageFileList(prj, pkg, revision=rev)
        for fil in file_list:
            if fil.endswith(".changes"):
                changelog = self.obs.getFile(prj, pkg, fil)
        return changelog

    def handle_wi(self, wid):
        """ actual job thread """
        wid.result = False

        missing = [name for name in ["project", "package"]
                if not getattr(wid.fields, name, None)]
        if missing:
            raise RuntimeError("Missing mandatory field(s): %s" %
                ", ".join(missing))

        self.setup_obs(wid.fields.ev.namespace)

        wid.fields.changelog = self.get_changes_file(
                wid.fields.project,
                wid.fields.package)

        wid.result = True
