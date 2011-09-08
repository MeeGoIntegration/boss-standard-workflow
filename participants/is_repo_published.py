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

from buildservice import BuildService



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
        """Setup the Buildservice instance.

        Using the namespace as an alias to the apiurl.
        """

        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    def is_published(self, project, repository=None, architecture=None):
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
            # At this point we have the repo/arch we want
            if not state == "published":
                result = False

        return result

    def handle_wi(self, wid):
        """Actual job thread."""

        # We may want to examine the fields structure
        if wid.fields.debug_dump:
            print wid.dump()

        wid.result = False

        self.setup_obs(wid.fields.ev.namespace)

        wid.result = self.is_published(wid.params.project,
                                       wid.params.repository,
                                       wid.params.arch)

