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
   trial_projct:
      The trial build area that was setup
   ev.project:
      The destination project of this submit request (only used in diagnostic error message)

:term:`Workitem` fields OUT:

:Returns:
   Removes trial_project
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

        # We may want to examine the fields structure
        if wid.fields.debug_dump:
            print wid.dump()

        wid.result = False

        obs = BuildService(oscrc=self.oscrc, apiurl=wid.fields.ev.namespace)

        try:
            wid.result = False
            core.delete_project(obs.apiurl, wid.fields.trial_project,
                                force=True, msg="Removed by BOSS")
            print "Trial area %s removed" % wid.fields.trial_project
            del(wid.fields.as_dict()["trial_project"])
            wid.result = True
        except HTTPError as err:
            if err.code == 403:
                print "Is the BOSS user (see /etc/skynet/oscrc) enabled as a"\
                      " maintainer in the project %s:Testing" \
                      % wid.fields.ev.project

            if err.code == 404:
                print "HTTPError 404 : The project is already gone"
                wid.result = True
                return

            raise err
