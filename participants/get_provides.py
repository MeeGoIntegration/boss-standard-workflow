#!/usr/bin/python
""" Participant to get list of binaries providing some package

"""
from collections import defaultdict
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

        targets = []
        if wid.params.repository:
            if wid.params.arch:
                targets = ["%s/%s" % (wid.params.repository, wid.params.arch)]
            else:
                targets = ["%s/%s" % (wid.params.repository, arch) for arch in
                        self.obs.getRepositoryArchs(project,
                            wid.params.repository)]
        else:
            if wid.params.arch:
                targets = [target for target in self.obs.getTargets(project) if
                        target.endswith("/%s" % wid.params.arch)]
            else:
                targets = self.obs.getTargets(project)

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
                    bininfo = self.obs.getBinaryInfo(project, target, package,
                            binary)
                    if bininfo.get("arch", "src") == "src":
                        continue
                    for name in bininfo.get("provides", []):
                        if name.split("=")[0].strip() == provide:
                            result[package][target].append(binary)
                            found = True
        if found:
            return result
        return None
