#!/usr/bin/python
"""Downloads image configuration RPM package(s) and extracts kickstart files.

Fetches all binary RPMs specified and extracts all .ks files from them to a
subdirectory in a configured prefix. All the files are then symlinked to the
prefix directory.


:term:`Workitem` fields IN

:Parameters:
    ev.namespace(string):
        Namespace to use, see here:
        http://wiki.meego.com/Release_Infrastructure/BOSS/OBS_Event_List
    image_configurations(dictionary):
        Dictionary of image configuration providing binaries as returned by
        get_provides participant.

:term:`Workitem` params IN:

:Parameters:
    project(string):
        Project to download kickstarts binaries from


:term:`Workitem` fields OUT

:Parameters:
    msg:
        Possible error messages

:Returns:
    result(Boolean):
       True if kickstart(s) were found, false otherwise
"""

import os, glob, shutil

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
        if ctrl.message == "start":
            self.deploy_prefix = ctrl.config.get("autoks", "ksroot")


    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Job thread."""

        if not isinstance(wid.fields.msg, list):
            wid.fields.msg = []
        if not wid.fields.image_configurations:
            print("Mandatory field 'image_configurations' missing")
            return

        if not wid.params.project:
            raise RuntimeError("Mandatory parameter 'project' missing")

        try:
            configurations = wid.fields.image_configurations.as_dict()
        except AttributeError:
            raise RuntimeError("Field 'image_configurations' is expected to be "
                    "a dictionary")

        self._download_kickstarts(wid.params.project, configurations)
        self._cleanup_symlinks()

        wid.result = True

    def _cleanup_symlinks(self):
        for ks in glob.glob(os.path.join(self.deploy_prefix, "*.ks")):
            if os.path.lexists(ks) and not os.path.exists(ks):
                os.unlink(ks)

    def _download_kickstarts(self, project, configurations):
        """Downloads RPM and extrack .ks files."""
        rpms = set()
        with Lab(prefix="get_kickstarts") as lab:
            # Download binaries
            if isinstance(project, str):
                project = project.encode('utf8')
            for package in configurations:
                if isinstance(package, str):
                    package = package.encode('utf8')
                for target in configurations[package]:
                    if isinstance(target, str):
                        target = target.encode('utf8')
                    for binary in configurations[package][target]:
                        if isinstance(binary, str):
                            binary = binary.encode('utf8')
                        rpms.add(self.download_binary(project, package,
                                target, binary, lab.path))

            for rpm in rpms:
                # deploy dir is the name of the rpm without the versions
                deploy_dir = os.path.join(self.deploy_prefix,
                             ".%s" % os.path.basename(rpm).rsplit("-", 2)[0])
                # Both release and devel ks share the same directory
                if not os.path.exists(deploy_dir):
                    os.mkdir(deploy_dir)
                # Extract kickstart files and copy to the deploy dir
                for fname in extract_rpm(rpm, lab.path, patterns=["*.ks"]):
                    shutil.copy(os.path.join(lab.path, fname), deploy_dir)
                    symlink_src = os.path.join(deploy_dir, os.path.basename(fname))
                    symlink_dst = os.path.join(self.deploy_prefix, os.path.basename(fname))
                    if os.path.lexists(symlink_dst):
                        os.unlink(symlink_dst)
                    os.symlink(symlink_src, symlink_dst)

        return
