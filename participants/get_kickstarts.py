#!/usr/bin/python
"""Downloads image configuration RPM package(s) and extracts kickstart files.

Fetches all binary RPMs produced by the specified package and extracts all .ks
files from them to workitem images list.


:term:`Workitem` fields IN

:Parameters:
    project:
        The configuration package is looked from this projects
    ev.actions(List):
        (Optional) If this is SR, look for the conf package in actions.
    ignore_ks:
        (Optional) List of kickstart file name patterns to ignore


:term:`Workitem` parameters IN

:Parameters:
    conf_package:
        OBS name of the configuration package


:term:`Workitem` fields OUT

:Parameters:
    images:
        List of image definition dictionaries. Dictionary will contain fields
          * "kickstart" with the kickstart file contents and
          * "name" with the kickstart file name without extension

:Returns:
    result(Boolean):
       True if kickstart(s) were found, false otherwise

"""
import os, re, shutil

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
        pass

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
        if wid.fields.ignore_ks is not None and \
                not isinstance(wid.fields.ignore_ks, list):
            raise RuntimeError("Field 'ignore_ks' has to be a list")
        ignore = [re.compile(pat) for pat in wid.fields.ignore_ks or []]

        # Find the package
        # If configuration package is in submit request sources, get it from
        # that project
        if wid.fields.ev.actions:
            for action in wid.fields.ev.actions:
                if action.get("sourcepackage", None) == package:
                    project = action["sourceproject"]
        targets = self.get_project_targets(project, wid=wid)

        images = []
        with Lab(prefix="ks_downloader") as lab:
            for fname in self._download_kickstarts(lab.path, project, package,
                    targets):
                ks_name = os.path.basename(fname)
                if [True for pattern in ignore if pattern.match(ks_name)]:
                    continue
                images.append({
                    "name": os.path.splitext(ks_name)[0],
                    "kickstart":lab.open(fname).read()})

        wid.fields.images = images
        if images:
            wid.result = True


    def _download_kickstarts(self, target_dir, project, package, targets):
        """Downloads RPMs for given package."""
        rpm_files = []
        for target in targets:
            for binary in self.get_binary_list(project, package, target):
                if not binary.endswith(".rpm") or binary.endswith(".src.rpm")\
                        or binary in rpm_files:
                    continue
                rpm_files.append(binary)
                self.download_binary(project, package, target, binary,
                        target_dir)
        ks_files = set()
        for rpm in rpm_files:
            ks_files.update(extract_rpm(rpm, target_dir, patterns=["*.ks"]))
        return ks_files
