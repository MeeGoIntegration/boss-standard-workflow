#!/usr/bin/python
"""Downloads image configuration RPM package(s) and extracts kickstart files.

Fetches all binary RPMs produced by the specified package and extracts all .ks
files from them to workitem images list.


:term:`Workitem` fields IN

:Parameters:
    ev.namespace(string):
        Namespace to use, see here:
        http://wiki.meego.com/Release_Infrastructure/BOSS/OBS_Event_List
    image_configurations(dictionary):
        Dictionary of image configuration providing binaries as returned by
        get_provides participant.
    ignore_ks:
        (Optional) List of kickstart file name patterns to ignore


:term:'Workitem' params IN:
    project(string):
        Project to download kickstarts binaries from


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
import os, re

from boss.obs import BuildServiceParticipant, RepositoryMixin
from boss.lab import Lab
from boss.rpm import extract_rpm


class ParticipantHandler(BuildServiceParticipant, RepositoryMixin):
    """Participant class as defined by the SkyNET API."""

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
        if not wid.fields.image_configurations:
            raise RuntimeError("Mandatory field 'image_configurations' missing")
        if not wid.params.project:
            raise RuntimeError("Mandatory parameter 'project' missing")

        if wid.fields.ignore_ks is not None and \
                not isinstance(wid.fields.ignore_ks, list):
            raise RuntimeError("Field 'ignore_ks' has to be a list")

        ignore = [re.compile(pat) for pat in wid.fields.ignore_ks or []]
        images = self._download_kickstarts(wid.params.project,
                wid.fields.image_configurations, ignore)

        wid.fields.images = images
        if images:
            wid.result = True


    def _download_kickstarts(self, project, configurations, ignore):
        """Downloads RPM and extrack .ks files."""
        images = []
        rpms = []
        ks_files = set()
        with Lab(prefix="ks_downloader") as lab:
            # Download binaries
            for package in configurations:
                for target in configurations[package]:
                    for binary in configurations[package][target]:
                        rpms.append(self.download_binary(project, package,
                                target, binary, lab.path))

            # Extract kickstart files
            for rpm in rpms:
                ks_files.update(extract_rpm(rpm, lab.path, patterns=["*.ks"]))
            
            # Read ks contents in images array
            for fname in ks_files:
                # TODO: normalize names to prevent collisions
                ks_name = os.path.basename(fname)
                if [True for pattern in ignore if pattern.match(ks_name)]:
                    continue
                images.append({
                    "name": os.path.splitext(ks_name)[0],
                    "kickstart": lab.open(fname).read()})

        return images
