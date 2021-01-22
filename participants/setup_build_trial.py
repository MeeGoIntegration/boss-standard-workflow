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

from boss.obs import BuildServiceParticipant
import collections
from lxml import etree
from copy import copy
import itertools


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

    def __missing__(self, key):
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
        if next_repo not in extra_paths:
            extra_paths[next_repo] = next_paths
        else:
            for path in next_paths:
                if path not in extra_paths[next_repo]:
                    extra_paths[next_repo].append(path)
    return extra_paths


def get_extra_paths(repolinks, prjmeta):
    """generates build paths to a project
    categorized by repos they will be added to
    """

    extra_paths = OrderedDefaultdict(list)
    project = prjmeta.get('name')
    for link_repo, link_archs in repolinks.iteritems():
        for repoelem in prjmeta.findall('repository'):
            repo = repoelem.get('name')
            for archelem in repoelem.findall('arch'):
                if archelem.text in link_archs:
                    x = (project, repo, archelem.text)
                    if (
                        link_repo not in extra_paths or
                        x not in extra_paths[link_repo]
                    ):
                        extra_paths[link_repo].append(
                            (project, repo, archelem.text)
                        )
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
                next_paths = _merge_paths(
                    get_extra_paths(repolinks, prjmeta), next_paths
                )
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
                    if target not in done:
                        finished = False
                        prjmeta = self.get_prjmeta(project)
                        next_paths = self.get_next_paths(
                            repolinks, prjmeta, repo
                        )
                        extra_paths = _merge_paths(extra_paths, next_paths)
                        done.add(target)
        return extra_paths

    def get_repolinks(
        self, project, prjmeta, exclude_repos=[], exclude_archs=[]
    ):
        """Get a description of the repositories to link to.
           Returns a dictionary where the repository names are keys
           and the values are lists of architectures."""

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
                repolinks[repo].append(arch)
            if not repolinks[repo]:
                del repolinks[repo]
        return repolinks

    def get_trials(self, trial_project, groups, suffix):

        trial_map = {}
        trial_groups = collections.defaultdict(set)
        if groups is None:
            return trial_map, trial_groups

        for name, prefixes in groups.items():
            for tgt in prefixes:
                if hasattr(tgt, "items"):
                    subtrial_map, subtrial_groups = self.get_trials(
                        trial_project, tgt, suffix
                    )
                    trial_map.update(subtrial_map)
                    trial_groups.update(subtrial_groups)
                    continue
                else:
                    expected = tgt + suffix
                    prj = copy(trial_project)
                    if name:
                        prj += ":%s" % name
                    trial_map[expected] = prj
                    trial_groups[prj].add(expected)

        return trial_map, trial_groups

    def calculate_trial(
        self, links, exclude_repos, exclude_archs, extra_path=None
    ):

        repolinks = collections.defaultdict(set)
        extra_paths = OrderedDefaultdict(list)
        flag_types = ["build", "publish"]
        flags = {}
        for link in links:
            prjmeta = self.get_prjmeta(link)
            for rl, archs in self.get_repolinks(
                link, prjmeta, exclude_repos, exclude_archs
            ).items():
                repolinks[rl].update(archs)

            for ftype in flag_types:
                flag = prjmeta.find(ftype)
                if flag is None:
                    continue
                for subflag in flag:
                    if not subflag.attrib:
                        flag.remove(subflag)
                if ftype not in flags:
                    flags[ftype] = flag
                else:
                    flags[ftype].extend(flag.getchildren())

        # if an extra build path is required,
        # find matching ones for the linked repos
        if extra_path:
            # extra_paths = get_extra_paths(repolinks, extra_path)
            # usually the above should be enough but for some reason OBS
            # descends down the chain of only the last build path in a repo,
            # therefore the recursion is done here until that behavior is fixed
            extra_paths = _merge_paths(
                extra_paths,
                self.get_extra_paths_recursively(repolinks, extra_path)
            )

        for link in links:
            extra_paths = _merge_paths(
                extra_paths,
                self.get_extra_paths_recursively(repolinks, link)
            )

        if extra_path:
            main_repo = extra_path
        elif links:
            main_repo = list(links)[0]

        for repo, paths in extra_paths.items():
            pos = None
            for path in paths:
                if path[0] == main_repo:
                    pos = paths.index(path)
                    break
            if pos:
                main_path = paths.pop(pos)
                paths.append(main_path)
                extra_paths[repo] = paths

        return repolinks, extra_paths, flags

    def add_self_refs(self, trial_project, repolinks, extra_paths):
        for repo, archs in repolinks.iteritems():
            for link_repo, link_archs in repolinks.iteritems():
                if repo == link_repo:
                    continue
                for arch in archs:
                    if arch in link_archs:
                        extra_paths[link_repo].insert(
                            0, (trial_project, repo, arch)
                        )
        return extra_paths

    def remove_invalid_paths(self, trial_project, extra_paths, targets):
        """This removes repositories that do not exists from the paths.

        Just a temporary solution untill someone has time to go through the
        logic and figure out where the non existing repos come from.
        """
        project_repos = {}
        for repo in extra_paths.keys():
            old_paths = extra_paths[repo]
            valid_paths = []
            for project, prepo, arch in old_paths:
                if project == trial_project and repo == prepo:
                    continue
                if project not in project_repos:
                    project_repos[project] = [
                        tuple(t.split('/'))
                        for t in self.obs.getTargets(project)
                    ]
                if (prepo, arch) in project_repos[project]:
                    valid_paths.append((project, prepo, arch))
            if valid_paths:
                extra_paths[repo] = valid_paths
            else:
                del extra_paths[repo]

            for project in list(targets):
                if project not in project_repos:
                    project_repos[project] = [
                        tuple(t.split('/'))
                        for t in self.obs.getTargets(project)
                    ]
                if repo not in [p[0] for p in project_repos[project]]:
                    targets.remove(project)

    def construct_trial(
        self, trial_project, actions,
        extra_path=None, extra_links=None,
        exclude_repos=[], exclude_archs=[], exclude_links=None
    ):
        mechanism = "localdep"
        targets = set([act['targetproject'] for act in actions])
        if not targets and extra_path:
            targets.add(extra_path)
        if exclude_links:
            targets = targets - exclude_links
        repolinks, extra_paths, flags = self.calculate_trial(
            targets, exclude_repos, exclude_archs, extra_path=extra_path
        )

        targets.update(
            path[0] for path in
            itertools.chain.from_iterable(extra_paths.values())
        )
        targets.update(extra_links)
        if exclude_links:
            targets = targets - exclude_links

        repolinks, extra_paths, flags = self.calculate_trial(
            targets, exclude_repos, exclude_archs, extra_path=extra_path
        )
        self.remove_invalid_paths(trial_project, extra_paths, targets)

        self.remove_invalid_paths(trial_project, extra_paths, targets)
        self.log.debug("extra_paths cleaned %s", extra_paths)

        # Create project link with build disabled
        result = self.obs.createProject(
            trial_project, repolinks,
            links=targets,
            paths=extra_paths,
            build=False,
            flags=[copy(flag) for flag in flags.values()],
            publish=False,
            mechanism=mechanism,
        )

        if not result:
            raise RuntimeError(
                "Something went wrong while creating build trial project %s" %
                trial_project
            )

        extra_paths = self.add_self_refs(trial_project, repolinks, extra_paths)
        self.remove_invalid_paths(trial_project, extra_paths, targets)

        result = self.obs.createProject(
            trial_project, repolinks,
            links=targets,
            paths=extra_paths,
            build=False,
            flags=[copy(flag) for flag in flags.values()],
            publish=False,
            mechanism=mechanism,
        )

        self.log.info("Trial area %s created" % trial_project)

        submits = [
            act['targetpackage'] for act in actions
            if act['type'] == 'submit'
        ]
        # Copy packages into trial area
        for act in actions:
            # handle delete requests using build disable flags
            if act['type'] == 'delete' and act['targetpackage'] not in submits:
                if "build" not in flags:
                    flags["build"] = etree.Element("build")
                flags["build"].append(
                    etree.Element(
                        "disable", {"package": act['targetpackage']}
                    )
                )

            if act['type'] == 'submit':
                self.obs.copyPackage(
                    self.obs.apiurl,
                    act['sourceproject'],
                    act['sourcepackage'],
                    self.obs.apiurl,
                    trial_project,
                    act['targetpackage'],
                    client_side_copy=False,
                    keep_maintainers=False,
                    keep_develproject=False,
                    expand=True,
                    revision=act['sourcerevision'],
                    comment="Trial build",
                )

        self.log.info("Starting trial build %s" % trial_project)
        # enable build
        result = self.obs.createProject(
            trial_project, repolinks,
            links=targets,
            paths=extra_paths,
            build=True,
            flags=[copy(flag) for flag in flags.values()],
            publish=True,
            mechanism=mechanism,
        )
        if not result:
            raise RuntimeError(
                "Something went wrong while enabling build "
                "for trial project %s" % trial_project
            )

        return targets

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Actual job thread."""

        if not wid.fields.ev.id:
            raise RuntimeError("Missing mandatory field 'ev.id'")
        if not wid.fields.ev.actions:
            raise RuntimeError("Missing mandatory field 'ev.actons'")
        rid = wid.fields.ev.id
        prj_prefix = wid.params.under or wid.fields.project
        trial_project = "%s:SR%s" % (prj_prefix, rid)
        actions = wid.fields.ev.actions
        build_trial_groups = wid.fields.build_trial.as_dict().get("groups", {})
        suffix = wid.fields.build_trial.suffix or ""
        trial_map, trial_groups = self.get_trials(
            trial_project, build_trial_groups, suffix
        )
        exclude_prjs = wid.fields.build_trial.exclude_prjs or []
        if suffix:
            exclude_prjs = [prj + suffix for prj in exclude_prjs]
        exclude_repos = wid.fields.exclude_repos or []
        exclude_archs = wid.fields.exclude_archs or []
        wid.result = False
        self.cache = {}
        # first construct main trial project
        main_actions = [
            act for act in actions
            if (act["targetproject"] in trial_groups[trial_project] and
                act["targetproject"] not in exclude_prjs)
        ]
        main_links = self.construct_trial(
            trial_project, main_actions,
            extra_path=wid.fields.build_trial.extra_path,
            extra_links=set(),
            exclude_repos=exclude_repos,
            exclude_archs=exclude_archs,
        )
        main_links.add(trial_project)
        wid.fields.build_trial.project = trial_project
        # then construct trial sub projects
        for trial_sub_project, targets in trial_groups.items():
            self.log.debug(
                "trial subproject %s targets %s", trial_sub_project, targets
            )
            if trial_sub_project == trial_project:
                continue
            sub_actions = [
                act for act in actions
                if (act["targetproject"] in targets and
                    act["targetproject"] not in exclude_prjs)
            ]
            self.construct_trial(
                trial_sub_project, sub_actions,
                extra_path=trial_project,
                extra_links=set(targets),
                exclude_repos=exclude_repos,
                exclude_archs=exclude_archs,
                exclude_links=main_links,
            )
        wid.fields.build_trial.subprojects = _normalize(trial_groups)
        wid.result = True
