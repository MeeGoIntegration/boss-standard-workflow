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

:term:`Workitem` params IN:

:Parameters:
   under:
      Name of subproject to run the trial under.

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
import collections
from lxml import etree
from copy import copy

sched_arch = {"i586":"i486", "armv8el":"armv7hl"}

class OrderedDefaultdict(collections.OrderedDict):
    def __init__(self, *args, **kwargs):
        if not args:
            self.default_factory = None
        else:
            if not (args[0] is None or callable(args[0])):
                raise TypeError('first argument must be callable or None')
            self.default_factory = args[0]
            args = args[1:]
        super(OrderedDefaultdict, self).__init__(*args, **kwargs)

    def __missing__ (self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = default = self.default_factory()
        return default

    def __reduce__(self):  # optional, for pickle support
        args = (self.default_factory,) if self.default_factory else ()
        return self.__class__, args, None, None, self.iteritems()

def _normalize(ds):
    """ converts a dict like object with sets for values to a dict of lists """
    for i in ds:
        ds[i] = list(ds[i])
        ds[i].reverse()
    return ds

def _merge_paths(extra_paths, next_paths):
    """ merge two dict like objects with sets for values """
    for next_repo, next_paths in next_paths.items():
        if not next_repo in extra_paths:
            extra_paths[next_repo] = next_paths
        else:
            for path in next_paths:
                if path not in extra_paths[next_repo]:
                    extra_paths[next_repo].append(path)
    return extra_paths

def get_extra_paths(repolinks, prjmeta):
    """ generates build paths to a project categorized by repos they will be added to """

    extra_paths = OrderedDefaultdict(list)
    project = prjmeta.get('name')
    for link_repo, link_archs in repolinks.iteritems():
        for repoelem in prjmeta.findall('repository'):
            repo = repoelem.get('name')
            if not repo == link_repo:
                continue
            for archelem in repoelem.findall('arch'):
                march = sched_arch[archelem.text]
                if archelem.text in link_archs and (march in project or march in repo):
                    x = (project, repo, archelem.text)
                    if link_repo not in extra_paths or x not in extra_paths[link_repo]:
                        extra_paths[link_repo].append((project, repo, archelem.text))
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

    def get_prjmeta(self, project):
        """ Fetch a project meta from cache or server """
        prjmeta = self.cache.get(project)
        if not prjmeta:
            prjmeta = etree.fromstring(self.obs.getProjectMeta(project))
            self.cache[project] = prjmeta
        return prjmeta

    def get_next_paths(self, repolinks, prjmeta, repo):
        next_paths = {}
        for repoelem in prjmeta.findall(".//repository[@name='%s']" % repo):
            for path in repoelem.findall("path"):
                next_project = path.get("project")
                prjmeta = self.get_prjmeta(next_project)
                next_paths = _merge_paths(get_extra_paths(repolinks, prjmeta), next_paths)
        return next_paths

    def get_extra_paths_recursively(self, repolinks, project):
        done = set()
        prjmeta = self.get_prjmeta(project)
        finished = False
        extra_paths = get_extra_paths(repolinks, prjmeta)
        while not finished:
            finished = True
            for _, paths in extra_paths.items():
                for project, repo, arch in paths:
                    target = "%s/%s/%s" % (project, repo, arch)
                    if not target in done:
                        finished = False
                        prjmeta = self.get_prjmeta(project)
                        next_paths = self.get_next_paths(repolinks, prjmeta, repo)
                        extra_paths = _merge_paths(extra_paths, next_paths)
                        done.add(target)
        return extra_paths

    def get_repolinks(self, wid, project, prjmeta):
        """Get a description of the repositories to link to.
           Returns a dictionary where the repository names are keys
           and the values are lists of architectures."""
        exclude_repos = wid.fields.exclude_repos or []
        exclude_archs = wid.fields.exclude_archs or []
    
        repolinks = {}
        for repoelem in prjmeta.findall('repository'):
            repo = repoelem.get('name')
            if repo in exclude_repos:
                continue
            repolinks[repo] = []
            for archelem in repoelem.findall('arch'):
                arch = archelem.text
                if arch in exclude_archs:
                    continue
                #if not sched_arch[arch] in repo:
                #    continue
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
        prj_prefix = wid.fields.project
        if wid.params.under:
            prj_prefix = wid.params.under
        trial_project = "%s:SR%s" % (prj_prefix, rid)
        wid.result = False

        mechanism = "localdep"
        if wid.fields.build_trial and wid.fields.build_trial.mechanism:
            mechanism = wid.fields.build_trial.mechanism

        links = set()
        for act in actions:
            links.add(act['targetproject'])

        self.cache = {}
        repolinks = collections.defaultdict(set)
        extra_paths = OrderedDefaultdict(list)
        flag_types = ["build", "publish"]
        flags = {}
        for link in links:
            prjmeta = self.get_prjmeta(link)
            for rl, archs in self.get_repolinks(wid, link, prjmeta).items():
                repolinks[rl].update(archs)

            for ftype in flag_types:
                flag = prjmeta.find(ftype)
                if flag is None:
                    continue
                for subflag in flag:
                    if not subflag.attrib:
                        flag.remove(subflag)
                if not ftype in flags:
                    flags[ftype] = flag
                else:
                    flags[ftype].extend(flag.getchildren())
                # handle delete requests using build disable flags
                if ftype == "build":
                    submits = [ act['targetpackage'] for act in actions if act['type'] == 'submit' ]
                    for act in actions:
                        if act['type'] == 'delete' and not act['deletepackage'] in submits:
                            flags[ftype].append(etree.Element("disable", {"package" : act['deletepackage']}))                    

        extra_path = None
        # if an extra build path is required, find matching ones for the linked repos
        if wid.fields.build_trial and wid.fields.build_trial.extra_path:
            extra_path = wid.fields.build_trial.extra_path
            # extra_paths = get_extra_paths(repolinks, extra_path)
            # usually the above should be enough but for some reason OBS descends
            # down the chain of only the last build path in a repo, therefore
            # the recursion is done here until that behavior is fixed
            extra_paths = _merge_paths(extra_paths, self.get_extra_paths_recursively(repolinks, extra_path))

        inject_repo = None
        for link, archs in repolinks.items():
            if len(archs) > 1 and "i586" in archs:
               inject_repo = link

        for link in links:
            extra_paths = _merge_paths(extra_paths, self.get_extra_paths_recursively(repolinks, link))

        if extra_path:
            main_repo = extra_path
        else:
            main_repo = list(links)[0]

        #extra_paths = _normalize(extra_paths) 
        for repo, paths in extra_paths.items():
            #paths.reverse()
            for path in paths:
                if path[0] == main_repo:
                    pos = paths.index(path)
                    break
            main_path = paths.pop(pos)
            paths.append(main_path)
            extra_paths[repo] = paths

        try:

            # Create project link with build disabled
            result = self.obs.createProject(trial_project, repolinks, 
                                            links=links,
                                            paths=extra_paths,
                                            build=False, flags=[ copy(flag) for ftype, flag in flags.items() ],
                                            publish=False, mechanism=mechanism)

            if not result:
                raise RuntimeError("Something went wrong while creating build trial project %s" % trial_project)

            if inject_repo:
                for link, archs in repolinks.items():
                    if not link == inject_repo:
                        for arch in archs:
                            path = (trial_project, inject_repo, arch)
                            if not link in extra_paths:
                                extra_paths[link] = []
                            if not path in extra_paths[link]:
                                extra_paths[link].append(path)
                            break

                result = self.obs.createProject(trial_project, repolinks, 
                                                links=links,
                                                paths=extra_paths,
                                                build=False, flags=[ copy(flag) for ftype, flag in flags.items() ],
                                                publish=False, mechanism=mechanism)

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
                                            links=links,
                                            paths=extra_paths,
                                            build=True, flags=[ copy(flag) for ftype, flag in flags.items() ],
                                            publish=True, mechanism=mechanism)
            if not result:
                raise RuntimeError("Something went wrong while enabling build for trial project %s" % trial_project)

        except HTTPError as err:
            if err.code == 403:
                self.log.info("Not allowed to create project %s" % trial)
            raise



