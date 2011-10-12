#!/usr/bin/python
"""Creates a new clean trial build area used for building the packages being
promoted against the target project. It is setup as a project link 
Read more about prj_links :
http://en.opensuse.org/openSUSE:Build_Service_Concept_project_linking

.. warning::
   The OBS user configured in the oscrc file used needs to have maintainership
   rights on the trial build parent project. For example if request 100 is
   promoting packages to Chalk:Trunk the trial project will be
   Chalk:Trunk:Trial:SR100 and Chalk:Trunk:Trial needs to already be setup with
   maintainer rights for the automation user

Usage::
  setup_build_trial :under => "Testing"

:term:`Param` fields IN:

:Parameters:
   under:
      Name of subproject to run the trial under. Defaults to "Trial" if not specified.

:term:`Workitem` fields IN:

:Parameters:
   ev.id:
      Submit request id
   ev.project:
      The destination project of this submit request

:term:`Workitem` fields OUT:

:Returns:
   build_trial.project (string):
      The trial build area that was setup - this is expected to be used by
      remove_build_trial
   result(Boolean):
      True if everything went OK, False otherwise.

"""

from buildservice import BuildService
from urllib2 import HTTPError

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
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        if not wid.fields.ev.id :
            wid.error = "Mandatory field 'ev.id' missing"
            wid.fields.msg.append(wid.error)
            raise RuntimeError(wid.error)

        obs = BuildService(oscrc=self.oscrc, apiurl=wid.fields.ev.namespace)
        if wid.params.under:
            trial = wid.params.under
        else:
            trial = "%s:Trial" % wid.fields.project

        wid.result = False
        trial_project = "%s:SR%s" % (trial, wid.fields.ev.id)

        try:
            result = obs.createProjectLink(wid.fields.project,
                                           wid.fields.repository,
                                           wid.fields.archs,
                                           trial_project)

            if result:
                wid.fields.build_trial.project = trial_project

            print "Trial area %s created" % wid.fields.build_trial.project
            wid.result = result
        except HTTPError as err:
            if err.code == 403:
                print "Is the BOSS user (see /etc/skynet/oscrc.conf) enabled" \
                      " as a maintainer in the project %s" % trial
            raise
