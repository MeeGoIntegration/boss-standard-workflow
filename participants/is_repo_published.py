#!/usr/bin/python
"""Checks the state of a project's repositories or single repository and
returns success if the repository has been published.

:term:`Workitem` params IN

:Parameters:
   project(string):
      The project to check
   repository(string):
      Optionally, the repository in above project. if not provided the state of
      all repositories in the project are checked
   arch(string):
      Optionally, the arch in above repository. if not provided the state of
      all archs in the repository are checked

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if repository(ies are) is published, False otherwise.

"""

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

    def is_published(self, project, repository=None, architecture=None, exclude_repos=[], exclude_archs=[]):
        """Check if a repository is published

        :param project: project name
        :type project: string
        :param repository: optional reposiory name
        :type repository: string or None
        :param architecture: optional architecture name
        :type architecture: string or None
        :rtype: bool
        """
        result = True
        # Returns dict {"repo/arch" : "state"}
        all_states = self.obs.getRepoState(project)
        for repo_arch, state in all_states.items():
            repo , arch = repo_arch.split("/")
            if repository and not repo == repository: 
                # skip unwanted repo
                continue
            if architecture and not arch == architecture:
                # skip unwanted arch
                continue
            if exclude_repos and repo in exclude_repos:
                continue
            if exclude_archs and arch in exclude_archs:
                continue
            # At this point we have the repo/arch we want
            # unpublished means that repository publishing is disabled
            if not state.endswith("published"):
                result = False

        return result

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Actual job thread."""

        wid.result = False

        wid.result = self.is_published(wid.params.project,
                                       wid.params.repository,
                                       wid.params.arch,
                                       wid.fields.exclude_repos,
                                       wid.fields.exclude_archs)

