#!/usr/bin/python
""" Marks the project of target SR to have the need for a nightly image.
:term:`Workitem` fields IN :
:Parameters:
   ev.project
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

    def check_and_mark_project(self, project, attribute):
        """
        Checks an OBS project for the existence of attribute needs_nightly_build.
        Return True if the project didn't have one and create the attibute.False
        otherwise.
        """
        if self.obs.projectAttributeExists(project, attribute):
            return False
        else:
            self.obs.createProjectAttribute(project,
                                           attribute)
            return True

    def handle_wi(self, wid):

        """ actual job thread """
        wid.status = False
        wid.fields.needs_build = False

        self.setup_obs(wid.fields.ev.namespace)
        if wid.params.delete:
            stat = self.obs.deleteProjectAttribute(wid.fields.ev.project,
                                           wid.params.attribute)
            if stat:
                wid.status = True
            else:
                wid.status = False
        else:
            if self.check_and_mark_project(wid.fields.ev.project,
                                           wid.params.attribute):
                wid.fields.needs_build = True
            else:
                wid.fields.needs_build = False
