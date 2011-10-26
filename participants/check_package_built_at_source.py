#!/usr/bin/python
"""
Check that makes sure package is built at source project against all
repositories and architectures defined in target project.

For each repository and archtitecture in target project the check looks for
matching repository and architecrture build status for each source package.
If status is:

  succeeded
    Everything is fine
  failed or not available
    Check fails
  anything else
    Check passes but informative message is recorded in workitem msg list


:term:`Workitem` fields IN :

:Parameters:
   ev.actions(list):
      the request :term:`actions`

:term:`Workitem` fields OUT :

:Returns:
   result(Boolean):
      True if the needed repository was found, False otherwise

Check respects the skip/warn values in [checks] section of packages boss.conf
for following keys:

    check_package_built_at_source:
        skip/warn for all package build checks

"""

from boss.checks import CheckActionProcessor
from boss.obs import BuildServiceParticipant, RepositoryMixin, OBSError
from urllib2 import HTTPError

def workitem_error(workitem, msg):
    """Convenience function for reporting unlikely errors."""
    if not workitem.fields.msg:
        workitem.fields.msg = []
    workitem.error = "[%s] %s" % (workitem.participant_name, msg)
    workitem.fields.msg.append(workitem.error)
    raise RuntimeError(workitem.error)

class ParticipantHandler(BuildServiceParticipant, RepositoryMixin):

    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        pass

    @CheckActionProcessor("check_package_built_at_source")
    def quality_check(self, action, wid):
        """Quality check implementation."""

        targets = []
        try:
            # Get build targets from target project and repository info from
            # source project
            for repo, info in self.get_target_repos(action, wid).iteritems():
                for arch in info["architectures"]:
                    targets.append("%s/%s" % (info["path"], arch))
            source_repos = self.get_source_repos(action, wid)
        except OBSError, exc:
            return False, "Failed to get repository information: %s" % exc
        try:
            # Get package build status in source project
            package_status = self.obs.getPackageStatus(action["sourceproject"],
                    action["sourcepackage"])
        except HTTPError, exc:
            return False, "Failed to get source package status: %s" % exc

        result = True
        msg = []
        for repo, info in source_repos.iteritems():
            for arch in info["architectures"]:
                for target in info["targets"]:
                    build_against =  "%s/%s" % (target, arch)
                    if build_against not in targets:
                        # We don't care about builds that are not against target
                        # or are already covered
                        continue
                    targets.remove(build_against)
                    source_build = "%s/%s" % (repo, arch)
                    # Check the source build status
                    status = package_status.get(source_build, "N/A")
                    if status != "succeeded":
                        msg.append("Build status is '%s' for %s (against %s)." %
                                (status, source_build, build_against))
                        if status != "excluded":
                            result = False

        if targets:
            msg.append("Not build against %s" % ", ".join(targets))
            result = False

        if msg:
            return result, " ".join(msg)

        return result, None

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Actual job thread."""
        wid.result = False

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        # Now check the prereq process fields
        if not wid.fields.ev.actions:
            workitem_error(wid, "need ev.actions")
        result = True
        for action in wid.fields.ev.actions:
            pkg_result, _ = self.quality_check(action, wid)
            result = result and pkg_result
        wid.result = result
