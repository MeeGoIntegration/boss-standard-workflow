#!/usr/bin/python
"""Report the build result status of a project

:term:`Workitem` fields IN :

:Parameters:
   project(string):
      The project name
   package(list of string):
      [optional] The package names
   excluded_repos(list of string):
      [optional] The names of repositories not to consider in the build trial
   excluded_archs(list of string):
      [optiona] The names of architectures not to consider in the build trial

:term:`Workitem` params IN

:Parameters:
   project(string):
      The final project, aka "Trunk"
   package(list of string):
      [optional] The package names
   excluded_repos(list of string):
      [optional] The names of repositories not to consider in the build trial
   excluded_archs(list of string):
      [optional] The names of architectures not to consider in the build trial

:term:`Workitem` fields OUT :

:Returns:
   result(Boolean):
      True if there were no new failures, False otherwise
   failures(list):
      A list of package names that have failed to build
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

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Actual job thread.

        Get new failures related to a build trial."""

        wid.result = False

        if not wid.fields.msg:
            wid.fields.msg = []

        if wid.params.project:
            prj = wid.params.project
        else:
            prj = wid.fields.project

        if wid.params.packages:
            pkgs = wid.params.package
        else:
            pkgs = wid.fields.packages or []

        if wid.params.exclude_repos:
            exclude_repos = wid.params.exclude_repos
        else:
            exclude_repos = wid.fields.exclude_repos or []

        if wid.params.exclude_archs:
            exclude_archs = wid.params.exclude_archs
        else:
            exclude_archs = wid.fields.exclude_archs or []

        failures = set()
        for repo in self.obs.getProjectRepositories(prj):
            if repo in exclude_repos:
                continue
            archs = self.obs.getRepositoryArchs(prj, repo)
            archs = [arch for arch in archs if arch not in exclude_archs]
            # Get results
            results = self.obs.getRepoResults(prj, repo)
            failures.update(self.get_failures(results, archs))

        # filter results
        if pkgs:
            failures = failures & set(pkgs)

        if len(failures):
            wid.fields.msg.append(
                "%s failed to build in %s" % (" ".join(failures), prj)
            )
            wid.fields.failures = list(failures)
        else:
            wid.result = True

    def get_failures(self, results, archs):
        """Compare two sets of results.

        :param results: The new results as returned by
          BuildService.getRepoResults()
        :param archs: list of architectures

        :returns: A list of failures
        """
        failures = {}
        for arch in archs:
            self.log.debug("Looking at %s", arch)
            for pkg in results[arch].keys():
                self.log.debug("now %s %s", pkg, results[arch][pkg])
                # If we succeed then continue to the next package.
                # In a link project, unbuilt packages from the link-source
                # are reported as 'excluded' (which is as good as success)
                # another OK state is 'disabled'
                if results[arch][pkg] in ["succeeded", "excluded", "disabled"]:
                    continue
                else:
                    # a broken new package is also a new failure
                    failures[pkg] = True
        return failures.keys()
