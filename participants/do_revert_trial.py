#!/usr/bin/python
"""Reverts the trial build area to a state where it can handle the next
requests's build trial.

.. warning::
   The OBS user configured in the oscrc file used needs to have maintainership
   rights on the trial build project.

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      Submit request data structure :term:`actions`
   ev.id:
      Submit request id

:term:`Workitem` params IN

:Parameters:
   build_in:
      The trial build area (project)
   linked(Boolean):
      Set it to True if the trial build area is a project Link to the
      destination. This will cause any binary packages to be deleted.
      Read more about prj_links :
      http://en.opensuse.org/openSUSE:Build_Service_Concept_project_linking

:term:`Workitem` fields OUT:

:Returns:
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

    def setup_obs(self, namespace):
        """Setup the Buildservice instance

        Using the namespace as an alias to the apiurl.
        """
        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    def revert_trial(self, wid):
        """Copy packages from trunk to testing.

          * The revert notes the intended request destination and copies the
            latest version from there (usually Trunk) back into the build_in
            project.
          * Later, if/when parallel build_in projects are used it may be
            important to correctly sync build_in from a potentially updated
            Trunk
          * If build_in is a project link we remove the packages and
            wipebinaries
        """

        wid.result = False
        rid = wid.fields.ev.id
        actions = wid.fields.ev.actions
        build_in = wid.params.build_in

        for act in actions:
            if wid.params.linked :
                self.obs.deletePackage(build_in, act['targetpackage'])
                self.obs.wipeBinaries(build_in)
            else:
                try:
                    self.obs.copyPackage(self.obs.apiurl,
                                         act['targetproject'],
                                         act['targetpackage'],
                                         self.obs.apiurl,
                                         build_in,
                                         act['targetpackage'],
                                         client_side_copy = False,
                                         keep_maintainers = False,
                                         keep_develproject = False,
                                         expand = False,
                                         comment = "Trial revert for \
                                                    request %s" % rid)
                except HTTPError, exp:
                    # If the package is not found in target, reverting is
                    # done by deleting it from build_in.
                    if exp.code == 404:
                        self.obs.deletePackage(build_in,
                                               act['targetpackage'])
                    else:
                        raise

        print "Revert trial for request %s" % rid
        wid.result = True

    def handle_wi(self, wid):
        """Actual job thread."""

        self.setup_obs(wid.fields.ev.namespace)
        self.revert_trial(wid)

