#!/usr/bin/python
"""Copies the set of packages that are being promoted by a submit request to
a trial build area.

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
      destination. This will cause any leftover binary packages to be wiped.
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

    def build_trial(self, wid):
        """Copy packages from source to build_in:

          * Since we are not doing a cross instance copy the src and dst
            apiurl are the same.
          * The request is made from the source to the eventual destination.
            So using the request_src project in the build_trial and copying to
            the build_in will work.
          * This also uses the specific version mentioned in the request.
          * if build_in is a project link clean it from any possible left over
            binaries.

        """

        wid.result = False
        rid = wid.fields.ev.id
        actions = wid.fields.ev.actions
        build_in = wid.params.build_in

        # wipeBinaries errors if there are no packages to wipe
        #if wid.params.linked:
        #    pkgs = self.obs.getPackageList(build_in)
        #    if pkgs:
        #        self.obs.wipeBinaries(build_in)
        #        for pkg in pkgs:
        #            self.obs.deletePackage(build_in, pkg)
   
        for act in actions:
            if act['type'] == 'submit':
                self.obs.copyPackage(self.obs.apiurl,
                                 act['sourceproject'],
                                 act['sourcepackage'],
                                 self.obs.apiurl,
                                 build_in,
                                 act['targetpackage'],
                                 client_side_copy = False,
                                 keep_maintainers = False,
                                 keep_develproject = False,
                                 expand = True,
                                 revision = act['sourcerevision'],
                                 comment = "Trial build for request %s" % rid)
            # TODO: figure out a way to simulate deletions in the trial build

        self.log.info("Trial build for request %s" % rid)
        wid.result = True

    def handle_wi(self, wid):
        """Actual job thread."""

        self.setup_obs(wid.fields.ev.namespace)
        try:
            self.build_trial(wid)
        except HTTPError as err:
            if err.code == 403:
                self.log.info("Is the BOSS user (see /etc/skynet/oscrc) enabled as a maintainer in the relevant project")
            raise err
