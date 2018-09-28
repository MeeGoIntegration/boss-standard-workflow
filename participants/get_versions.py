from rpmUtils.miscutils import splitFilename
from boss.obs import BuildServiceParticipant, RepositoryMixin


class ParticipantHandler(BuildServiceParticipant, RepositoryMixin):
    """Participant class as defined in SkyNET API."""

    def __init__(self):
        """Initializator."""

        BuildServiceParticipant.__init__(self)

    def handle_wi_control(self, ctrl):
        """Control job thread."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Control participant thread."""
        pass

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Handle workitem."""
        if not wid.fields.versions:
            return
        versions = wid.fields.versions.as_dict()
        for pkg, d in versions.items():
            target = "%s/%s" % (d["repository"], d["arch"])

            for binary in self.obs.getBinaryList(d["project"], target, pkg):
                n, v, r, e, a = splitFilename(binary)
                if n != d.get("binary", pkg):
                    continue
                bininfo = self.obs.getBinaryInfo(d["project"],
                                                 target, pkg, binary)
                versions[pkg].update({"version": v,
                                      "release": r.split("."),
                                      "epoch": e,
                                      "arch": a,
                                      "summary": bininfo["summary"],
                                      "description": bininfo["description"]})

        wid.fields.versions = versions
