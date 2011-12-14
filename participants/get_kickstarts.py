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


:term:`Workitem` params IN:

:Parameters:
    project(string):
        Project to download kickstarts binaries from


:term:`Workitem` fields OUT

:Parameters:
    kickstarts:
        List of dictionaries. Dictionary will contain fields
          * "contents" with the kickstart file contents
          * "basename" with the kickstart file name
          * "basedir" with the path of kickstarts file
    msg:
        Possible error messages

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
        if not isinstance(wid.fields.msg, list):
            wid.fields.msg = []
        if not wid.fields.image_configurations:
            raise RuntimeError("Mandatory field 'image_configurations' missing")
        if not wid.params.project:
            raise RuntimeError("Mandatory parameter 'project' missing")

        if wid.fields.ignore_ks is not None and \
                not isinstance(wid.fields.ignore_ks, list):
            raise RuntimeError("Field 'ignore_ks' has to be a list")

        try:
            configurations = wid.fields.image_configurations.as_dict()
        except AttributeError:
            raise RuntimeError("Field 'image_configurations' is expected to be "
                    "a dictionary")

        ignore = [re.compile(pat) for pat in wid.fields.ignore_ks or []]

        wid.fields.kickstarts, errors = self._download_kickstarts(wid.params.project,
                configurations, ignore)
        if wid.fields.kickstarts:
            wid.result = True
        if errors:
            wid.fields.msg.append("Errors while downloading kickstarts: %s" %
                    ", ".join(errors))


    def _download_kickstarts(self, project, configurations, ignore):
        """Downloads RPM and extrack .ks files."""
        kickstarts = []
        errors = []
        rpms = set()
        with Lab(prefix="get_kickstarts") as lab:
            # Download binaries
            for package in configurations:
                for target in configurations[package]:
                    for binary in configurations[package][target]:
                        rpms.add(self.download_binary(project, package,
                                target, binary, lab.path))

            for rpm in rpms:
                # Extract kickstart files
                found = False
                for fname in extract_rpm(rpm, lab.path, patterns=["*.ks"]):
                    # Read ks contents in images array
                    basedir, basename = os.path.split(fname)
                    if [True for pattern in ignore if pattern.match(basename)]:
                        continue
                    kickstarts.append({
                        "basedir": basedir,
                        "basename": basename,
                        "contents": lab.open(fname).read()})
                    found = True
                if not found:
                    errors.append("%s did not contain .ks files" %
                            os.path.basename(rpm))


        return kickstarts, errors
