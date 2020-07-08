#!/usr/bin/python3
""" This participant is used to select test packages that can be added or installed 
to an image. Selection can be based on "*-test" naming convention or "Provides: qa-tests"
convention.
When using the naming convention:
For a set of packages (persumably being promoted) any
<packagename>-tests binary package produced by them are selected.
In addition their reverse dependencies are worked out and then all
<packagename>-tests binary packages produced by them are also selected.
When using the provides convention:
For a set of packages (persumably being promoted) any
binary package that provide qa-tests produced by them are selected.
In addition their reverse dependencies are worked out and then all
binary packages produced by them that provide qa-tests are also selected.

:term:`Workitem` fields IN

:Parameters:
    ev.namespace(string):
        Namespace to use, see here:
        http://wiki.meego.com/Release_Infrastructure/BOSS/OBS_Event_List
    qa.test_patterns(dict):
        patterns which shall be expanded and added to qa.selected_test_packages
	{ Pattern : Project }

:term:`Workitem` params IN

:Parameters:
    project(string):
        OBS project where binaries are searched
    package(string):
        (optional) OBS package where to limit the search
    repository(string):
        (optional) OBS project repository to limit the search
    arch(string):
        (optional) OBS project repository architecture to limit the search
    using(list of strings):
        The selection convention to use. "name", "provides" or "pattern"
    allow_recursive(bool) TODO: NOT YET IMPLEMENTED!
        shall the patterns expanding be recursive: True recusive, False do not
        expand patterns within the pattern

:term:`Workitem` fields OUT

:Returns:
   result(boolean):
      True if everything was OK, False otherwise.
   qa.selected_test_packages(dict of lists):
      Extends the dict of packages going to be included in the image

"""

from urllib.error import HTTPError
from boss.obs import BuildServiceParticipant
from copy import copy

class ParticipantHandler(BuildServiceParticipant):

    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass

    def select_bpkgs(self, project, package, target, using):
        binaries = self.obs.getBinaryList(project, target, package)

        selected = {}
        for binary in binaries:
            binary_name = "-".join(binary.split("-")[:-2])
            if using == "provides":
                bininfo = self.obs.getBinaryInfo(project, target, package,
                                                 binary)
                if bininfo.get("arch", "src") == "src":
                    continue

                provs = []
                for name in bininfo.get("provides", []):
                    provs.append(name.split("=")[0].strip())

                if "qa-tests" in provs:
                    selected[binary_name] = provs

            elif using == "name":
                if binary_name.endswith("-tests"):
                    selected[binary_name] = []

        return selected

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """ actual job thread """
        wid.result = False

        if not wid.fields.msg:
            wid.fields.msg = []

        missing = [name for name in ["project", "using"]
                if not getattr(wid.params, name, None)]
        if missing:
            raise RuntimeError("Missing mandatory field(s): %s" %
                    ", ".join(missing))

        tmp_using = wid.params.using
	using = []

        # old version expected a string, now it should be a list of strings
	if isinstance(tmp_using, list):
            using = tmp_using
	else:
            using.append(tmp_using)

        selected = {}
        for use in using:
            if not use in ["name", "provides", "pattern"]:
                raise RuntimeError("Invalid using parameter %s" % use)

            if use == "name" or use == "provides":
                project = wid.params.project
                packages = [wid.params.package] if wid.params.package \
                    else self.obs.getPackageList(project)

                packages = set(packages)

                # get all project targets (repo/arch)
                try:
                    avail_targets = self.obs.getTargets(project)
                except HTTPError as exc:
                    if exc.code == 404:
                        raise RuntimeError("Project not found '%s'" % project)
                    raise

                targets = []
                # filter targets based on params
                for target in avail_targets:
                    repo, arch = target.split("/")
                    if wid.params.repository and repo != wid.params.repository:
                        continue
                    if wid.params.arch and arch != wid.params.arch:
                        continue
                    targets.append(target)

                if not targets:
                    return

                new_packages = copy(packages)
                # get reverse dependencies of each package
                for target in targets:
                    repo, arch = target.split("/")
                    for pkg in new_packages:
                        for pkg_revdep in self.obs.getPackageReverseDepends(project, repo,
                                                                            pkg, arch):
                            packages.add(pkg_revdep)

                # get binary packages of each package and select ones that match the criteria
                if not wid.fields.qa:
                    wid.fields.qa = {"selected_test_packages" : {} }
                else:
                    qa = wid.fields.qa.as_dict()
                    if "selected_test_packages" in qa:
                        selected.update(qa["selected_test_packages"])

                for target in targets:
                    for package in packages :
                        selected.update(self.select_bpkgs(project, package, target, use))

            elif use == "pattern":
                if not wid.fields.qa.test_patterns:
                    raise RuntimeError("using 'pattern' is requested, but mandatory field is missing: qa.test_patterns")

                patterns = wid.fields.qa.test_patterns.as_dict()
                expanded_patterns = self.obs.expandPatterns(patterns, depth = 4)
                print("expanded_patterns:")
                print(expanded_patterns)
                for pattern, props in expanded_patterns.items():
                    for rpmpgk in props['requires']:
                        selected.update({rpmpgk: props['provides']})

            wid.fields.qa.selected_test_packages = selected

        wid.fields.msg.append('Test packages selected using %s: %s' %
                              (", ".join(using), ", ".join(selected.keys())))

        wid.result = True
