#!/usr/bin/python
"""Compare the build result status of two projects used to make sure
build results are same as or better than the current results in the
destination project.

:term:`Workitem` fields IN :

:Parameters:
   project(string):
      The final project, aka "Trunk"
   excluded_repos(list of string):
      The names of repositories not to consider in the build trial
   excluded_archs(list of string):
      The names of architectures not to consider in the build trial

:term:`Workitem` params IN

:Parameters:
   build_in(string):
      The trial build area (project)

:term:`Workitem` fields OUT :

:Returns:
   result(Boolean):
      True if there were no new failures, False otherwise
   new_failures(list):
      A list of package names that have failed during the trial build
      but had built successfully in the destination project
"""
import itertools
from collections import defaultdict
from buildservice import BuildService

def get_new_failures(trial_results, orig_results, archs, acts):
    """Compare two sets of results.

    :param trial_result: The new results as returned by
      BuildService.getRepoResults()
    :param orig_results: The old results as returned by
      BuildService.getRepoResults()
    :param archs: list of architectures

    :returns: A list of new failures
    """
    new_failures = {}
    old_failures = {}
    reqs = defaultdict(set)
    for act in acts:
        reqs[act["type"]].add(act["targetpackage"])

    for arch in archs:
        print "Looking at %s" % arch
        if not arch in trial_results:
            continue
        for pkg in trial_results[arch].keys():
            print "now %s %s" % (pkg, trial_results[arch][pkg])
            # If we succeed then continue to the next package.
            # In a link project, unbuilt packages from the link-source
            # are reported as 'excluded' (which is as good as success)
            if trial_results[arch][pkg] in ["succeeded", "excluded", "disabled"]:
                continue
            # if a pkg has failed in trial build and is in the
            # original results...
            if pkg in orig_results[arch]:
                print "orig %s %s" % (pkg, orig_results[arch][pkg])
            # ... and had built successfuly there...
                if not orig_results[arch][pkg] == trial_results[arch][pkg]:
                    # ...then this is a new failure
                    new_failures[pkg] = True
                else:
                    old_failures[pkg] = True
            else:
                # a broken new package is also a new failure
                new_failures[pkg] = True

    for fail in new_failures.keys():
        if "delete" in reqs and fail in reqs["delete"]:
            if "submit" in reqs:
                if not fail in reqs["submit"]:
                    del(new_failures[fail])
            else:
                del(new_failures[fail])

    return (new_failures.keys(), old_failures.keys())

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

        Using namespace as an alias to the apiurl.
        """

        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    def check_trial(self, prj, targets, acts, exc):

        exclude_repos, exclude_archs = exc

        new_failures = set()
        old_failures = set()
        for target_prj in targets:
            for target_repo in self.obs.getProjectRepositories(target_prj):
                if target_repo in exclude_repos:
                    continue
                archs = self.obs.getRepositoryArchs(target_prj, target_repo)
                archs = [arch for arch in archs if arch not in exclude_archs]
                print archs
                # Get the repository of the build trial which builds against the
                # required target repo in the target prj
                #build_in_repo = self.obs.getTargetRepo(build_in_prj, target_prj,
                #                                       target_repo, archs)
                # Get trial build results
                trial_results = self.obs.getRepoResults(prj, target_repo)
                # Get destination results
                orig_results = self.obs.getRepoResults(target_prj, target_repo)
                # compare them and return new failures
                comparison = get_new_failures(trial_results, orig_results, archs, acts)
                new_failures.update(comparison[0])
                old_failures.update(comparison[1])

        return new_failures - old_failures

    def build_trial_results(self, wid):
        """Main function to get new failures related to a build trial."""

        wid.result = False

        if not wid.fields.msg:
            wid.fields.msg = []

        exclude_repos = wid.fields.exclude_repos or []
        exclude_archs = wid.fields.exclude_archs or []

        trial_project = wid.fields.build_trial.project
        trial_subprjs = wid.fields.build_trial.as_dict().get('subprojects', {})

        subtargets = list(itertools.chain.from_iterable(trial_subprjs.values()))
        actions = [act for act in wid.fields.ev.actions if act["targetproject"] not in subtargets]
        targets = [act["targetproject"] for act in actions]

        messages = []
        all_fails = []

        fails = self.check_trial(trial_project, targets, actions, exc=(exclude_repos, exclude_archs))
        if fails:
            all_fails.extend(fails)
            wid.fields.msg.append("During the trial build in %s, %s failed to"\
                                  " build" %
                                  (trial_project, " ".join(fails)))
        else:
            wid.fields.msg.append("Trial build of packages in %s successful" % trial_project)

        for trial_sub, subtargets in trial_subprjs.items():
            subactions = [act for act in wid.fields.ev.actions if act["targetproject"] in subtargets]
            fails = self.check_trial(trial_sub, subtargets, subactions, exc=(exclude_repos, exclude_archs))
            if fails:
                all_fails.extend(fails)
                wid.fields.msg.append("During the trial build in %s, %s failed to build" %
                                      (trial_sub, " ".join(fails)))
            else:
                wid.fields.msg.append("Trial build of packages in %s successful" % trial_sub)


        if all_fails:
            wid.fields.new_failures = all_fails
        else:
            wid.result = True

    def handle_wi(self, wid):
        """Actual job thread."""

        self.setup_obs(wid.fields.ev.namespace)
        self.build_trial_results(wid)

