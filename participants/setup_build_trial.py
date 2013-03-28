#!/usr/bin/python
"""Creates a new clean trial build area used for building the packages being
promoted against the target project. It is setup as a project link 
Read more about prj_links :
http://en.opensuse.org/openSUSE:Build_Service_Concept_project_linking

.. warning::
   The OBS user configured in the oscrc file used needs to have maintainership
   rights on the target project.

:term:`Workitem` fields IN:

:Parameters:
   ev.id:
      Submit request id
   ev.actions(list):
      Submit request data structure :term:`actions`
   project:
      The destination project of this submit request
   exclude_repos:
      Names of repositories not to include in the build trial
   exclude_archs:
      Names of architectures not to include in the build trial
   build_trial.extra_path:
      Name of a project to use for extra build paths.
   build_trial.mechanism:
      Mechanism of rebuilding in the trial project link (localdep / all).

:term:`Workitem` fields OUT:

:Returns:
   build_trial.project (string):
      The trial build area that was setup - this is expected to be used by
      remove_build_trial
   result(Boolean):
      True if everything went OK, False otherwise.

"""

from urllib2 import HTTPError

from boss.obs import BuildServiceParticipant
from collections import defaultdict
from lxml import etree

def _normalize(ds):
    """ converts a dict like object with sets for values to a dict of lists """
    for i in ds:
        ds[i] = list(ds[i])
        ds[i].reverse()
    return ds

def _merge_paths(extra_paths, next_paths):
    """ merge two dict like objects with sets for values """
    for next_repo, next_paths in next_paths.items():
        extra_paths[next_repo] = extra_paths[next_repo] | next_paths
    return extra_paths

def get_extra_paths(repolinks, prjmeta):
    """ generates build paths to a project categorized by repos they will be added to """

    extra_paths = defaultdict(set)
    project = prjmeta.get('name')
    for link_repo, link_archs in repolinks.iteritems():
        for repoelem in prjmeta.findall('repository'):
            repo = repoelem.get('name')
            for archelem in repoelem.findall('arch'):
                march = archelem.text
                if march == "armv8el":
                    march = "armv7hl"
                elif march == "armv7el":
                    march = "armv7l"
                if archelem.text in link_archs and (march in project or march in repo):
                    extra_paths[link_repo].add((project, repo))
    return extra_paths

class ParticipantHandler(BuildServiceParticipant):
    """Participant class as defined by the SkyNET API."""

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        pass

    def get_prjmeta(self, project, cache):
        """ Fetch a project meta from cache or server """
        if not project in cache:
            cache[project] = etree.fromstring(self.obs.getProjectMeta(project))

    def get_next_paths(self, repolinks, prjmeta, repo, cache):
        next_paths = {}
        for repoelem in prjmeta.findall(".//repository[@name='%s']" % repo):
            for path in repoelem.findall("path"):
                next_project = path.get("project")
                self.get_prjmeta(next_project, cache)
                next_paths = get_extra_paths(repolinks, cache[next_project])
        return next_paths

    def get_extra_paths_recursively(self, repolinks, project):
        done = set()
        cache = {}
        self.get_prjmeta(project, cache)
        finished = False
        extra_paths = get_extra_paths(repolinks, cache[project])
        while not finished:
            finished = True
            for _, paths in extra_paths.items():
                for project, repo in paths:
                    target = "%s/%s" % (project, repo)
                    if not target in done:
                        finished = False
                        self.get_prjmeta(project, cache)
                        next_paths = self.get_next_paths(repolinks, cache[project], repo, cache)
                        extra_paths = _merge_paths(extra_paths, next_paths)
                        done.add(target)
        return extra_paths

    def get_repolinks(self, wid, project):
        """Get a description of the repositories to link to.
           Returns a dictionary where the repository names are keys
           and the values are lists of architectures."""
        exclude_repos = wid.fields.exclude_repos or []
        exclude_archs = wid.fields.exclude_archs or []
    
        repolinks = {}
        cache = {}
        self.get_prjmeta(project, cache)
        for repoelem in cache[project].findall('repository'):
            repo = repoelem.get('name')
            if repo in exclude_repos:
                continue
            repolinks[repo] = []
            for archelem in repoelem.findall('arch'):
                arch = archelem.text
                if arch in exclude_archs:
                    continue
                repolinks[repo].append(arch)
            if not repolinks[repo]:
                del repolinks[repo]
        return repolinks

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Actual job thread."""

        if not wid.fields.ev.id:
            raise RuntimeError("Missing mandatory field 'ev.id'")
        if not wid.fields.ev.actions:
            raise RuntimeError("Missing mandatory field 'ev.actons'")
        rid = wid.fields.ev.id
        actions = wid.fields.ev.actions
        trial_project = "%s:Trial:SR%s" % (wid.fields.project, rid)
        wid.result = False

        mechanism = "localdep"
        if wid.fields.build_trial and wid.fields.build_trial.mechanism:
            mechanism = wid.fields.build_trial.mechanism

        repolinks = self.get_repolinks(wid, wid.fields.project)
         # if an extra build path is required, find matching ones for the linked repos
        extra_paths = None
        if wid.fields.build_trial and wid.fields.build_trial.extra_path:
            extra_path = wid.fields.build_trial.extra_path
            # extra_paths = get_extra_paths(repolinks, extra_path)
            # usually the above should be enough but for some reason OBS descends
            # down the chain of only the last build path in a repo, therefore
            # the recursion is done here until that behavior is fixed
            extra_paths = self.get_extra_paths_recursively(repolinks, extra_path)
            extra_paths = _normalize(extra_paths)

        try:
            # Create project link with build disabled
            result = self.obs.createProject(trial_project, repolinks, 
                                            link=wid.fields.project,
                                            paths=extra_paths,
                                            build=False,
                                            publish=False, mechanism=mechanism)

            if not result:
                raise RuntimeError("Something went wrong while creating build trial project %s" % trial_project)

            wid.fields.build_trial.project = trial_project
            self.log.info("Trial area %s created" % wid.fields.build_trial.project)
        
            # Copy packages into trial area
            for act in actions:
                if act['type'] == 'submit':
                    self.obs.copyPackage(self.obs.apiurl,
                                         act['sourceproject'],
                                         act['sourcepackage'],
                                         self.obs.apiurl,
                                         trial_project,
                                         act['targetpackage'],
                                         client_side_copy = False,
                                         keep_maintainers = False,
                                         keep_develproject = False,
                                         expand = True,
                                         revision = act['sourcerevision'],
                                         comment = "Trial build for request %s" % rid)

            self.log.info("Starting trial build for request %s" % rid)
            # enable build
            result = self.obs.createProject(trial_project, repolinks,
                                            link=wid.fields.project,
                                            paths=extra_paths,
                                            build=True,
                                            publish=True)
            if not result:
                raise RuntimeError("Something went wrong while enabling build for trial project %s" % trial_project)

        except HTTPError as err:
            if err.code == 403:
                self.log.info("Not allowed to create project %s" % trial)
            raise



