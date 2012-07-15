#!/usr/bin/python
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
    using(string):
        The selection convention to use. "name" or "provides"

:term:`Workitem` fields OUT

:Returns:
   result(boolean):
      True if everything was OK, False otherwise.
   qa.selected_packages(dict of lists):
      Extends the dict of packages going to be included in the image

"""

from urllib2 import HTTPError
from boss.obs import BuildServiceParticipant

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
            if using == "provides":
                bininfo = self.obs.getBinaryInfo(project, target, package,
                                                 binary)
                if bininfo.get("arch", "src") == "src":
                    continue

                provs = []
                for name in bininfo.get("provides", []):
                    provs.append(name.split("=")[0].strip())

                if "qa-tests" in provs:
                    selected[binary] = provs

            elif using == "name":
                if binary.endswith('-tests'):
                    selected[binary] = []

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

        using = wid.params.using

        if not using in ["name", "provides"]:
            raise RuntimeError("Invalid using parameter %s" % using)

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

        # get reverse dependencies of each package
        for target in targets:
            repo, arch = target.split("/")
            for pkg in packages:
                for pkg_revdep in self.obs.getPackageReverseDepends(project, repo,
                                                                    pkg, arch):
                    packages.update(pkg_revdep)

        # get binary packages of each package and select ones that match the criteria
        selected = {}
        for target in targets:
            for package in packages :
                selected = self.select_bpkgs(project, package, target, using)

        if not wid.fields.qa:
            wid.fields.qa = {"selected_packages" : {} }

        wid.fields.qa.selected_packages = selected

        wid.fields.msg.append('Test packages selected using %s: %s' %
                              (using, ", ".join(selected.keys())))

        wid.result = True
