#!/usr/bin/python
"""Downloads image configuration RPM package(s) and extracts kickstart files.

Fetches all binary RPMs produced by the specified package and extracts all .ks
files from them to directory specified by 'storage' configuration value.


:term:`Workitem` parametes IN

:Parameters:
    conf_package:
        OBS name of the configuration package
    path:
        (Optional) Path to create under the 'storage' directory for storing the
        .ks files.


:term:`Workitem` fields IN

:Parameters:
    project:
        The configuration package is looked from this projects
    ev.actions(List):
        (Optional) If this is SR, look for the conf pacakge in actions.


:term:`Workitem` fields OUT

:Parameters:
    kickstart_files:
        List of filenames stored under 'storage' directory


:Returns:
    result(Boolean):
       True if kicstart(s) were found, false otherwise

"""
import os, shutil

from boss.obs import BuildServiceParticipant, RepositoryMixin
from boss.lab import Lab
from boss.rpm import extract_rpm


class ParticipantHandler(BuildServiceParticipant, RepositoryMixin):
    """Participant class as defined by the SkyNET API."""

    def __init__(self):
        self.storage_path = None
        super(ParticipantHandler, self).__init__()

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        if ctrl.message == "start":
            if ctrl.config.has_option("download_kickstarts", "storage"):
                self.storage_path = ctrl.config.get("download_kickstarts",
                        "storage")
            else:
                raise RuntimeError("Missing mandatory config option "
                        "[download_kickstarts] storage")

            if not os.path.exists(self.storage_path):
                os.makedirs(self.storage_path)
            elif not os.path.isdir(self.storage_path):
                raise RuntimeError("Storage path '%s' is not a directory" %
                        self.storage_path)
            elif not os.access(self.storage_path, os.W_OK):
                raise RuntimeError("Storage path '%s' is not writable" %
                        self.storage_path)


    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Job thread."""
        wid.result = False
        if not wid.params.conf_package:
            raise RuntimeError("Mandatory parameter 'conf_package' missing")
        if not wid.fields.project:
            raise RuntimeError("Mandatory field 'project' missing")
        project = wid.fields.project
        package = wid.params.conf_package

        # Use given subdirectory or use workflowid
        # TODO: Maybe support some substitutions in the path parameter
        path = wid.params.path or wid.wfid
        os.makedirs(os.path.join(self.storage_path, path))

        # Find the package
        # If configuration package is in submit request sources, get it from
        # that project
        if wid.fields.ev.actions:
            for action in wid.fields.ev.actions:
                if action.get("sourcepackage", None) == package:
                    project = action["sourceproject"]
        targets = self.get_project_targets(project, wid=wid)

        ks_files = []
        with Lab() as lab:
            for fname in self._download_kickstarts(lab, project, package,
                    targets):
                source = os.path.join(lab.path, fname)
                destination = os.path.join(self.storage_path, path,
                        os.path.split(fname)[1])
                print "Moving %s to %s" % (source, destination)
                shutil.move(source, destination)
                ks_files.append(destination)
            if ks_files:
                wid.result = True
                wid.fields.kickstarts = ks_files


    def _download_kickstarts(self, lab, project, package, targets):
        """Downloads RPMs for given package."""
        rpm_files = []
        for target in targets:
            for binary in self.get_binary_list(project, package, target):
                if not binary.endswith(".rpm") or binary.endswith(".src.rpm")\
                        or binary in rpm_files:
                    continue
                rpm_files.append(binary)
                self.download_binary(project, package, target, binary,
                        lab.path)
        ks_files = set()
        for rpm in rpm_files:
            ks_files.update(extract_rpm(rpm, lab.path, patterns=["*.ks"]))
        return ks_files
