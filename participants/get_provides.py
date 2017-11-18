#!/usr/bin/python
"""Participant to get list of binaries providing some package (real or virtual)

:term:`Workitem` fields IN:

:Parameters:
    ev.namespace(string):
        Namespace to use, see here:
        http://wiki.meego.com/Release_Infrastructure/BOSS/OBS_Event_List

:term:'Workitem' params IN:

:Parameters:
    provide(string):
        Package name to search for
    project(string):
        OBS project where binaries are searched
    package(string):
        (optional) OBS package where to limit the search
    repository(string):
        (optional) OBS project repository to limit the search
    arch(string):
        (optional) OBS project repository architecture to limit the search
    field(string):
        (optional) Workitem field to store the result, defaults to 'provides'

:term:`Workitem` fields OUT:

:Returns:
    result(Boolean):
        True if providing binaries were found
    <field>(dictionary):
        Dictionary containing the information about binaries that provide
        requested package

If any of the optional parameters 'package', 'repository' or 'arch' is not
given, all combinations matching the other given parameters in target project
are searched. Providing only project means that all binaries for all packages in
all repositories and architectures in that project are searched for matching
providers.

The returned information field will contain dictionary with following format::

    {
    "package_name":
        {
        "<repository name>/<architecture>": [<list of binary rpm names>],
        ...
        },
    ...
    }

If no binaraies providing the requested name were found, the information field
is not set and worktiem result will be False.

"""
from collections import defaultdict
from urllib2 import HTTPError
from boss.obs import BuildServiceParticipant

class ParticipantHandler(BuildServiceParticipant):
    """Participant class as defined by the SkyNET API"""

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        pass

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Actual work thread"""
        wid.result = False
        project = wid.params.project
        if project is None:
            raise RuntimeError("Missing mandatory parameter 'project'")
        provide = wid.params.provide
        if provide is None:
            raise RuntimeError("Missing mandatory parameter 'provide'")

        packages = [wid.params.package] if wid.params.package \
                else self.obs.getPackageList(project)

        try:
            avail_targets = self.obs.getTargets(project)
        except HTTPError as exc:
            if exc.code == 404:
                raise RuntimeError("Project not found '%s'" % project)
            raise
        targets = []
        for target in avail_targets:
            repo, arch = target.split("/")
            if wid.params.repository and repo != wid.params.repository:
                continue
            if wid.params.arch and arch != wid.params.arch:
                continue
            targets.append(target)

        if not targets:
            return

        result = self.__get_provides(project, packages, targets, provide)
        if result:
            field = wid.params.field or "provides"
            setattr(wid.fields, field, result)
            wid.result = True

    def __get_provides(self, project, packages, targets, provide):
        """Fetch the providing binary info."""
        result = {}
        found = False
        for package in packages:
            result[package] = defaultdict(list)
            for target in targets:
                binaries = self.obs.getBinaryList(project, target, package)
                for binary in binaries:
                    self.log.info("Checking %s from %s in %s" % ( binary, package, target))
                    try:
                        bininfo = self.obs.getBinaryInfo(project, target,
                                                         package, binary)
                    except Exception, exc:
                        print "Skipping %s:%s" % (package, exc)

                    if bininfo.get("arch", "src") == "src":
                        continue
                    for name in bininfo.get("provides", []):
                        self.log.info("provides %s" % name)
                        if name.split("=")[0].strip() == provide:
                            self.log.info("found %s" % provide)
                            result[package][target].append(binary)
                            found = True
        if found:
            return result
        return None
