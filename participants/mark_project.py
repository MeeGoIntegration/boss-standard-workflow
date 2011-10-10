#!/usr/bin/python
""" Marks the project of target SR to have the need for a nightly image.
:term:`Workitem` fields IN :
:Parameters:
   ev.project
         Project to mark, usually the target project of the SR.
   delete:
         Delete the attribute from project
:Parameters:
   :term:`Workitem` fields OUT :

:Returns:
   result(Boolean):
      True if the project was marked for nightly builds or if the projects
      attribute was deleted successfully. False if the project already has
      nightly builds attribute enabled or if the project attribute for nightly
      builds was not deleted successfully.
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

    def check_and_mark_project(self, project):
        """
        Checks an OBS project for the existence of attribute needs_nightly_build.
        Return True if the project didn't have one and mark it so, False
        otherwise.
        """
        if self.obs.checkProjectAttribute(project, "needs_nightly_build"):
            return False
        else:
            self.obs.toggleProjectAttribute(project,
                                           "needs_nightly_build",
                                           delete=False)
            return True

    def handle_wi(self, wid):

        """ actual job thread """
        wid.result = False
        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.setup_obs(wid.fields.ev.namespace)
        if wid.fields.delete:
            stat = self.obs.toggleProjectAttribute(wid.fields.ev.project,
                                           "needs_nightly_build",
                                           delete=True)
            if stat:
                wid.fields.needs_build = True
            else:
                wid.fields.needs_build = False
        else:
            if self.check_and_mark_project(wid.fields.ev.project):
                wid.fields.needs_build = True
            else:
                wid.fields.needs_build = False