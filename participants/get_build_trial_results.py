#!/usr/bin/python
"""Compare the build result status of two projects used to make sure
build results are same as or better than the current results in the
destination project.

:term:`Workitem` fields IN :

:Parameters:
   ev.project(string):
      The final project, aka "Trunk"
   repository(string):
      The name of the repository in "Trunk" against which packages should build
   archs(list):
      The architectures we care about (i586, armv7l etc..)

:term:`Workitem` params IN

:Parameters:
   build_in(string):
      The trial build area (project)
   repository(string):
      Optionally, the repository in above project. if not provided the state of
      all repositories in the project are checked
   arch(string):
      Optionally, the arch in above repository. if not provided the state of
      all archs in the repository are checked

:term:`Workitem` fields OUT :

:Returns:
   result(Boolean):
      True if there were no new failures, False otherwise
   new_failures(list):
      A list of package names that have failed during the trial build
      but had built successfully in the destination project
"""

from buildservice import BuildService

def get_new_failures(trial_results, orig_results, archs):
    """Compare two sets of results.

    :param trial_result: The new results as returned by
      BuildService.getRepoResults()
    :param orig_results: The old results as returned by
      BuildService.getRepoResults()
    :param archs: list of architectures

    :returns: A list of new failures (per arch?).
    """
    new_failures = {}
    for arch in archs:
        print "Looking at %s" % arch
        for pkg in trial_results[arch].keys():
            print "now %s %s" %(pkg, trial_results[arch][pkg])
            # If we succeed then continue to the next package.
            # In a link project, unbuilt packages from the link-source
            # are reported as 'excluded' (which is as good as success)
            if trial_results[arch][pkg] in [ "succeeded", "excluded"]:
                continue
            # if a pkg has failed in trial build and is in the
            # original results...
            if pkg in orig_results[arch]:
                print "orig %s %s" %(pkg, orig_results[arch][pkg])
            # ... and had built successfuly there...
                if orig_results[arch][pkg] == "succeeded":
                    # ...then this is a new failure
                    new_failures[pkg] = True
            else:
                # a broken new package is also a new failure
                new_failures[pkg] = True
    return new_failures.keys()

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

    def build_trial_results(self, wid):
        """Main function to get new failures related to a build trial."""

        wid.result = False

        if not wid.fields.msg:
            wid.fields.msg = []

        target_prj = wid.fields.project
        target_repo = wid.fields.repository
        archs = wid.fields.archs
        build_in_prj = wid.params.build_in
        arch = wid.params.arch

        # pylint: disable=E1101
        # Get the repository of the build trial which builds against the
        # required target repo in the target prj
        build_in_repo = self.obs.getTargetRepo(build_in_prj, target_prj,
                                               target_repo, archs)
        # Get trial build results
        trial_results = self.obs.getRepoResults(build_in_prj, build_in_repo)
        # Get destination results
        orig_results = self.obs.getRepoResults(target_prj, target_repo)
        # pylint: enable=E1101
        # compare them and return new failures
        new_failures = get_new_failures(trial_results, orig_results, archs)

        if len(new_failures):
            wid.fields.msg.append("During the trial build in %s, %s failed to"\
                                  " build for one of the archs : %s" %
                                  (build_in_prj, " ".join(new_failures),
                                   " ".join(archs)))
            wid.fields.new_failures = new_failures
        else:
            wid.fields.msg.append("Trial build of packages in %s successful" %
                            build_in_prj)
            wid.result = True


    def handle_wi(self, wid):
        """Actual job thread."""

        # We may want to examine the fields structure
        if wid.fields.debug_dump:
            print wid.dump()

        self.setup_obs(wid.fields.ev.namespace)
        self.build_trial_results(wid)

