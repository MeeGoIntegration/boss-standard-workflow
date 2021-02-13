#!/usr/bin/python
""" This participants gets the whole changelog of a certain package from the
OBS changes file cotained in it.

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

from boss.obs import BuildServiceParticipant


class ParticipantHandler(BuildServiceParticipant):

    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass

    def get_changes_file(self, prj, pkg, rev=None):

        """ Get a package's changes file """

        changelog = ""
        file_list = self.obs.getPackageFileList(prj, pkg, revision=rev)
        for fil in file_list:
            if fil.endswith(".changes"):
                changelog = self.obs.getFile(prj, pkg, fil)
        return changelog

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """ actual job thread """
        wid.result = False

        missing = [
            name for name in ["project", "package"]
            if not getattr(wid.fields, name, None)
        ]
        if missing:
            raise RuntimeError(
                "Missing mandatory field(s): %s" % ", ".join(missing)
            )

        wid.fields.changelog = self.get_changes_file(
            wid.fields.project, wid.fields.package
        )

        wid.result = True
