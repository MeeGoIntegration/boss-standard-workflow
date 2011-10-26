#!/usr/bin/python
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
    def _process_action(self, action, wid):
        """Check valid repositories for single action."""
        msg = []
        targets = {}
        try:
            target_repos = self.get_target_repos(action, wid)
            source_repos = self.get_source_repos(action, wid)
        except OBSError, exc:
            return False, "Failed to get repository information: %s" % exc
        # Get expected build targets
        for repo, info in target_repos.iteritems():
            targets[info["path"]] = info["architectures"]

        for repo, info in source_repos.iteritems():
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
        for repo, archs in targets.iteritems():
            msg.append("No repository which builds only against %s [%s]." %
                    (repo, ", ".join(archs)))
        if msg:
            return False, " ".join(msg)
        return True, None

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """ actual job thread """
        wid.result = False
        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        if not wid.fields.ev or not wid.fields.ev.actions:
            raise RuntimeError("Missing mandatory field ev.actions")

        result = True
        checked_projects = []
        for action in wid.fields.ev.actions:
            project = action.get("sourceproject", None)
            if not project or project in checked_projects:
                # Check operates on project only so we don't need to run it for
                # each package
                continue
            checked_projects.append(project)
            valid, _ = self._process_action(action, wid)
            result = result and valid
        wid.result = result
