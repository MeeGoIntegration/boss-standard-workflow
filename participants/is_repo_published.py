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

import datetime
from boss.obs import BuildServiceParticipant

class State(object):
    """Represents a project source and publish state cached for a set time"""

    def __init__(self, obs, project):
        self.checked = None
        #FIXME: make it configurable
        self.lifetime = datetime.timedelta(seconds=300)
        self._obs = obs
        self.project = project
        self._source_state = None
        self._publish_states = None

    @property
    def expired(self):
        """indicates whether this state is expired and should be refreshed"""

        return self.checked is None or \
               self.checked + self.lifetime < datetime.datetime.now()

    @property
    def publish_states(self):
        """caching property representing the publish state of a project"""

        if self.expired:
            print "refreshing publish state of %s" % self.project
            # Returns dict {"repo/arch" : "state"}
            publish_states = {}
            all_states = self._obs.getRepoState(self.project)
            for repo_arch, state in all_states.items():
                repo , arch = repo_arch.split("/")
                # unpublished means that repository publishing is disabled
                publish_states[(repo, arch)] = state.endswith("published")
            self._publish_states = publish_states

        return self._publish_states

    @property
    def source_state(self):
        """caching property representing the source state of a project"""

        if self.expired:
            print "refreshing source state of %s" % self.project
            states = {}
            for package in self._obs.getPackageList(self.project):
                if package == '_pattern':
                    continue

                states[package] = False
                try:
                    _ = self._obs.getPackageFileList(self.project, package)
                    states[package] = True
                except Exception, exc:
                    print exc

            self._source_state = states

        return self._source_state

    def ready(self, repository=None, architecture=None, exclude_repos=None,
                    exclude_archs=None, packages=None):
        """Decides wether a project is ready to be used based on criteria"""

        ready = True
        for repo_arch, state in self.publish_states.items():
            repo, arch = repo_arch
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
            ready = ready and state

        print "publish state was %s" % ready

        if ready and not packages is None:
            # refresh state in case we are expired
            _ = len(self.source_state.keys())
            # get reference to source_state dict
            source_state = self.source_state
            # if not packages were specified care about all of them
            if not packages:
                packages = source_state.keys()
            
            for package in packages:
                ready = ready and source_state.get(package, True)
                if not ready:
                    print "%s not ready" % package
                    break

            print "source state was %s" % ready

        if self.expired:
            self.checked = datetime.datetime.now()
            print "state refreshed at %s, expires after %s" % \
                  ( self.checked, self.lifetime )

        return ready

class StateRegistry(object):
    """An in-memory registry of project states"""

    def __init__(self):
        self._states = {}

    def register(self, obs, project):
        """Register an obs project"""

        if not project in self._states:
            print "registering %s" % project
            self._states[project] = State(obs, project)
        return self._states[project]

class ParticipantHandler(BuildServiceParticipant):
    """Participant class as defined by the SkyNET API."""

    def __init__(self):

        BuildServiceParticipant.__init__(self)
        # start with empty project state registry
        self.registry = StateRegistry()

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        pass

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Actual job thread."""

        wid.result = False

        # Decide which packages to care about when checking source state
        # empty list will mean checking all packages
        # this is useful for checking trial build project
        packages = set()
        # OBS request with actions
        if wid.fields.ev and wid.fields.ev.actions:
            for action in wid.fields.ev.actions:
                # only check submit actions
                if action["type"] == "submit":
                    # if we are checking state of target project just skip
                    # target package could be non-existent or broken and this
                    # SR is fixing it for example
                    if wid.params.project == action['targetproject']:
                        packages = None
                        break
                    # if we are checking state of source project use
                    # sourcepackage name
                    elif wid.params.project == action['sourceproject']:
                        packages.add(action['sourcepackage'])

        state = self.registry.register(self.obs, wid.params.project)
        wid.result = state.ready(wid.params.repository,
                                 wid.params.arch,
                                 wid.fields.exclude_repos,
                                 wid.fields.exclude_archs,
                                 packages)

