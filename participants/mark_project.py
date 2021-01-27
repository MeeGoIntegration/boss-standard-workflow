#!/usr/bin/python
""" Marks the project of target SR to have the need for a nightly image.
:term:`Workitem` fields IN :
:Parameters:
   project
         Project to mark, usually the target project of the SR.
:term:`Workitem` parameters IN :
   delete:
         Delete the attribute from project
   attribute:
         Attribute to be created, checked or deleted
:Parameters:
   :term:`Workitem` fields OUT :

:Returns:
   needs_build(Boolean):
      True if the project was marked for nightly builds. False if the project
      already has specified attribute enabled.
   status(Boolean):
      True if the project was deleted succesfully. False otherwise
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

    def check_and_mark_project(self, project, attribute):
        """
        Checks an OBS project for the existence of attribute
        needs_nightly_build.

        Return True if the project didn't have one and create the attibute.
        False otherwise.
        """
        if self.obs.projectAttributeExists(project, attribute):
            return False
        else:
            self.obs.createProjectAttribute(
                project, attribute)
            return True

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):

        """ actual job thread """
        wid.status = False
        wid.fields.needs_build = False

        if wid.params.delete:
            stat = self.obs.deleteProjectAttribute(
                wid.fields.project, wid.params.attribute)
            if stat:
                wid.status = True
            else:
                wid.status = False
        else:
            if self.check_and_mark_project(
                    wid.fields.project, wid.params.attribute):
                wid.fields.needs_build = True
            else:
                wid.fields.needs_build = False
