#!/usr/bin/python
"""Removes a trial build area used for building the packages being
promoted against the target project. It is setup as a project link 
Read more about prj_links :
http://en.opensuse.org/openSUSE:Build_Service_Concept_project_linking

.. warning::
   The OBS user configured in the oscrc file used needs to have maintainership
   rights on the trial build parent project. For example if request 100 is
   promoting packages to Chalk:Trunk the trial project will be
   Chalk:Trunk:Testing:SR100 and Chalk:Trunk:Testing needs to be setup with
   proper rights

:term:`Workitem` fields IN:

:Parameters:
   build_trial.project:
      The trial build area that was setup

:term:`Workitem` fields OUT:

:Returns:
   build_trial.project:
      Cleared left empty
   result(Boolean):
      True if everything went OK, False otherwise.

"""

from buildservice import BuildService
from urllib2 import HTTPError
from osc import core

class ParticipantHandler(object):
    """Participant class as defined by the SkyNET API."""

    def __init__(self):
        self.oscrc = None
        self.obs = None

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")

    def handle_wi(self, wid):
        """Actual job thread."""

        wid.result = False

        if not wid.fields.build_trial or not wid.fields.build_trial.project :
            raise RuntimeError("Missing mandatory field 'build_trial.project'")

        obs = BuildService(oscrc=self.oscrc, apiurl=wid.fields.ev.namespace)

        try:
            wid.result = False
            core.delete_project(obs.apiurl, wid.fields.build_trial.project,
                                force=True, msg="Removed by BOSS")
            self.log.info("Trial area %s removed" % wid.fields.build_trial.project)
            del(wid.fields.build_trial.as_dict()["project"])
            wid.result = True
        except HTTPError as err:
            if err.code == 403:
                self.log.info("Is the BOSS user (see /etc/skynet/oscrc) enabled as a"\
                              " maintainer in %s or its parent?" \
                              % wid.fields.build_trial.project)

            if err.code == 404:
                self.log.info("HTTPError 404 : The project is already gone")
                wid.result = True
                return

            raise err
