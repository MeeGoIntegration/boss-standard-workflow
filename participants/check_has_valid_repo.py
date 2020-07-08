#!/usr/bin/python3
"""Check submit request source projects for valid repositories.

* For each repository in target project, there should be a repository in source
  project which builds only against the target repository.
* These source project repositories should have at least the same architectures
  as the target repository they build against.


:term:`Workitem` fields IN :

:Parameters:
   ev.actions(list):
      the request :term:`actions`

:term:`Workitem` fields OUT :

:Returns:
   result(Boolean):
      True if the needed repositories were found, False otherwise

"""

from boss.checks import CheckActionProcessor
from boss.obs import BuildServiceParticipant, RepositoryMixin, OBSError

class ParticipantHandler(BuildServiceParticipant, RepositoryMixin):

    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass


    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass

    @CheckActionProcessor("check_has_valid_repo", operate_on="project")
    def _process_action(self, action, wid, checked):
        """Check valid repositories for single action."""
        # Check operates on project only so we don't need to run it for
        # each package
        if (action["sourceproject"], action["targetproject"]) in checked:
            return True, None
        checked.add((action["sourceproject"], action["targetproject"]))

        msg = []
        targets = {}
        try:
            target_repos = self.get_target_repos(action, wid)
            source_repos = self.get_source_repos(action, wid)
        except OBSError as exc:
            return False, "Failed to get repository information: %s" % exc

        source_states = self.obs.getRepoState(action["sourceproject"])

        # Get expected build targets
        for repo, info in target_repos.items():
            targets[info["path"]] = info["architectures"]

        for repo, info in source_repos.items():
            if len(info["targets"]) != 1:
                # Repository should build only against single target
                continue
            builds_against = info["targets"][0]
            if builds_against not in targets:
                # Build target is not in target project
                continue
            # We have our target, lets check architectures
            archs = set(targets.pop(builds_against))
            missing_archs = archs.difference(info["architectures"])
            if missing_archs:
                msg.append("Repository %s missing architectures %s." %
                        (repo, ", ".join(missing_archs)))

        # Was there missing targets?
        for repo, archs in targets.items():
            msg.append("No repository which builds only against %s [%s]." %
                    (repo, ", ".join(archs)))
        if msg:
            msg.append("More information at http://wiki.meego.com/"\
                       "Getting_started_with_OBS#Adding_repositories")
            return False, " ".join(msg)
        return True, None

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """ actual job thread """
        wid.result = False

        if not wid.fields.ev or not wid.fields.ev.actions:
            raise RuntimeError("Missing mandatory field ev.actions")

        result = True
        checked_projects = set()
        for action in wid.fields.ev.actions:
            valid, _ = self._process_action(action, wid, checked_projects)
            result = result and valid
        wid.result = result
