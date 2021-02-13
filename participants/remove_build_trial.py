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

from urllib2 import HTTPError
from osc import core

from boss.obs import BuildServiceParticipant


class ParticipantHandler(BuildServiceParticipant):
    """Participant class as defined by the SkyNET API."""

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        pass

    def _delete_project(self, prj):
        try:
            # TODO move this to BuildService.deleteProject()
            core.delete_project(
                self.obs.apiurl, prj, force=True, msg="Removed by BOSS"
            )
            self.log.info("Trial area %s removed" % prj)
        except HTTPError as err:
            if err.code == 403:
                self.log.info(
                    "Is the BOSS user (see /etc/skynet/oscrc) enabled "
                    "as a maintainer in %s or its parent?" % prj
                )

            elif err.code == 404:
                self.log.info("HTTPError 404 : %s is already gone" % prj)

            else:
                raise err

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Actual job thread."""

        if not wid.fields.build_trial or not wid.fields.build_trial.project:
            raise RuntimeError("Missing mandatory field 'build_trial.project'")

        for prj in wid.fields.build_trial.as_dict().get("subprojects", []):
            if prj == wid.fields.build_trial.project:
                continue
            self._delete_project(prj)

        self._delete_project(wid.fields.build_trial.project)
