#!/usr/bin/python3
""" Updates package patterns for the target project. The patterns are
defined as XML files in a specific package. This participant downloads
that package, extracts all .xml files from the rpm and submits each
of them to OBS a pattern for the target project.

Patterns are special objects in OBS which add packages to groups. These groups
are called patterns. They are automatically generated for RPM repositories.
When installing a pattern, its packages are automatically pulled in. Patterns
are used in eg. kickstart files.

:term:`Workitem` fields IN:

:Parameters:
    ev.namespace(string):
        Namespace to use, see here:
        http://wiki.meego.com/Release_Infrastructure/BOSS/OBS_Event_List
    patterns(dictionary):
        Dictionary of pattern providing binaries as returned by get_provides
        participant.


:term:'Workitem' params IN:
    project(string):
        Project to update patterns to (and take groups package from)
    clean(Boolean):
        Whether to remove old patterns no longer included in the patterns package


:term:`Workitem` fields OUT:

:Returns:
    result(Boolean):
        True if the update was successfull
    msg(list):
        List of error messages

"""
import os

from boss.lab import Lab
from boss.obs import BuildServiceParticipant
from boss.rpm import extract_rpm


class ParticipantHandler(BuildServiceParticipant):
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
        """Actual job thread."""
        wid.result = False
        if not isinstance(wid.fields.msg, list):
            wid.fields.msg = []
        if not wid.fields.patterns:
            raise RuntimeError("Missing mandatory field 'patterns'")
        if not wid.params.project:
            raise RuntimeError("Missing mandatory parameter 'project'")
        patterns = wid.fields.patterns.as_dict()
        project = wid.params.project

        orig_patterns = self.obs.getProjectPatternsList(project)
        uploaded_patterns = set()

        result = True
        for package in patterns:
            for target in patterns[package]:
                for binary in patterns[package][target]:
                    done, errors = self.__update_patterns(
                            project, package, target, binary)
                    uploaded_patterns.update(done)
                    if errors:
                        result = False
                        wid.fields.msg.extend(errors)
                    elif not done:
                        result = False
                        wid.fields.msg.append(
                            "No patterns found in %s %s %s" %
                            (project, target, binary))

        wid.result = result

        # only remove old patterns if we were asked to, and no errors
        # occured while uploading
        if wid.params.clean and not errors:
            removed, errors = self.__clean_patterns(
                project, orig_patterns, uploaded_patterns)
            if removed:
                wid.fields.msg.append(
                    "removed old patterns: %s" % " ".join(removed))
            if errors:
                wid.fields.msg.extend(errors)

    def __update_patterns(self, project, package, target, binary):
        """Extracts patterns from rpm and uploads them to project.

        :returns: uploaded pattern names and error messages
        :rtype: tuple(list, list)
        """
        uploaded = []
        errors = []
        with Lab(prefix="update_patterns") as lab:
            # Download the rpm
            try:
                self.obs.getBinary(
                    project, target, package, binary, lab.real_path(binary))
            except Exception as exc:
                self.log.exception("Failed to download %s", binary)
                errors.append("Failed to download %s: %s" % (binary, exc))
            if errors:
                return uploaded, errors
            # Extract pattern (xml) files from the rpm
            self.log.debug(lab.real_path(binary))
            for xml in extract_rpm(lab.real_path(binary), lab.path, ["*.xml"]):
                pattern = os.path.basename(xml)
                try:
                    # chop .xml from name
                    if pattern.endswith(".xml"):
                        pattern = pattern[:-4]

                    # Update pattern to project
                    self.obs.setProjectPattern(
                        project, lab.real_path(xml), name=pattern)
                    uploaded.append(pattern)
                except Exception as exc:
                    self.log.exception("Failed to upload %s", pattern)
                    errors.append("Failed to upload %s: %s" % (pattern, exc))
        return uploaded, errors

    def __clean_patterns(self, project, orig_patterns, uploaded_patterns):
        removed = []
        errors = []
        for old_pattern in orig_patterns:
            if old_pattern in uploaded_patterns:
                continue
            try:
                self.obs.deleteProjectPattern(project, old_pattern)
                removed.append(old_pattern)
            except Exception as exc:
                self.log.exception("Failed to delete %s", old_pattern)
                errors.append("Failed to delete %s: %s" % (old_pattern, exc))
        return removed, errors
