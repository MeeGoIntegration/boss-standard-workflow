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

:term:`Workitem` fields IN:

:Parameters:
   ev.id:
      Submit request id
   project:
      The destination project of this submit request
   exclude_repos:
      Names of repositories not to include in the build trial
   exclude_archs:
      Names of architectures not to include in the build trial

:term:`Workitem` params IN:

:Parameters:
   under:
      Name of subproject to run the trial under.
      Defaults to "Trial" if not specified.

:term:`Workitem` fields OUT:

:Returns:
   build_trial.project (string):
      The trial build area that was setup - this is expected to be used by
      remove_build_trial
   result(Boolean):
      True if everything went OK, False otherwise.

"""

from urllib2 import HTTPError

from buildservice import BuildService

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

    def get_repolinks(self, wid, project):
        """Get a description of the repositories to link to.
           Returns a dictionary where the repository names are keys
           and the values are lists of architectures."""
        exclude_repos = wid.fields.exclude_repos or []
        exclude_archs = wid.fields.exclude_archs or []

        repolinks = {}
        for repo in self.obs.getProjectRepositories(project):
            if repo in exclude_repos:
                continue
            repolinks[repo] = []
            for arch in self.obs.getRepositoryArchs(project, repo):
                if arch in exclude_archs:
                    continue
                repolinks[repo].append(arch)
            # Skip whole repo if no archs were included
            if not repolinks[repo]:
                del repolinks[repo]
        return repolinks

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Actual job thread."""

        if not wid.fields.ev.id:
            raise RuntimeError("Missing mandatory field 'ev.id'")

        if wid.params.under:
            trial = wid.params.under
        else:
            trial = "%s:Trial" % wid.fields.project

        wid.result = False
        trial_project = "%s:SR%s" % (trial, wid.fields.ev.id)

        repolinks = self.get_repolinks(wid, wid.fields.project)
        try:
            result = self.obs.createProjectLink(wid.fields.project,
                                               repolinks,
                                               trial_project)

            if result:
                wid.fields.build_trial.project = trial_project

            self.log.info("Trial area %s created" % wid.fields.build_trial.project)
            wid.result = result
        except HTTPError as err:
            if err.code == 403:
                self.log.info("Is the BOSS user (see /etc/skynet/oscrc.conf) enabled" \)
                      " as a maintainer in the project %s" % trial
            raise
