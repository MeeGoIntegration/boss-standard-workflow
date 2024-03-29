#!/usr/bin/python
""" Updates various meta aspects of an OBS object:
* Project meta
* Project config

Project meta defines the project name, title, description, repositories etc..
Project config can control how and which packages are used / build in
a project.

All validation is left up to the receiving OBS.

:term:`Workitem` fields IN:

:Parameters:
    ev.namespace(string):
        Namespace to use, see here:
        http://wiki.meego.com/Release_Infrastructure/BOSS/OBS_Event_List
    prjmeta(dictionary):
        Dictionary of project meta providing binaries as returned by
        get_provides participant.
    prjconf(dictionary):
        Dictionary of project config providing binaries as returned by
        get_provides participant.

:term:'Workitem' params IN:
    project(string):
        Project to update meta to

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
from osc import core


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
        wid.result = True
        if not isinstance(wid.fields.msg, list):
            wid.fields.msg = []

        if not wid.params.project:
            raise RuntimeError("Missing mandatory parameter 'project'")
        project = wid.params.project

        if wid.fields.prjconf:
            prjconf = wid.fields.prjconf.as_dict()
            uploaded, errors = self.__update_meta(project, prjconf, "prjconf")
            if uploaded:
                wid.fields.msg.extend([
                    "Updated %s in %s" % (upload, project)
                    for upload in uploaded
                ])
            if errors:
                wid.fields.msg.extend(errors)
            #    wid.result = False

        if wid.fields.prjmeta:
            prjmeta = wid.fields.prjmeta.as_dict()
            uploaded, errors = self.__update_meta(project, prjmeta, "prj")
            if uploaded:
                wid.fields.msg.extend([
                    "Updated %s in %s" % (upload, project)
                    for upload in uploaded
                ])
            if errors:
                wid.fields.msg.extend(errors)
            #    wid.result = False

    def __update_meta(self, project, providers, metatype):
        """Extracts a meta xml from rpm and uploads them to project.

        :returns: uploaded pattern names and error messages
        :rtype: tuple(list, list)
        """
        uploaded = []
        errors = []
        for package, targets in providers.items():
            for target, binaries in targets.items():
                for binary in binaries:
                    with Lab(prefix=metatype) as lab:
                        # Download the rpm
                        try:
                            self.obs.getBinary(project, target, package,
                                               binary, lab.real_path(binary))
                        except Exception as exc:
                            self.log.exception("Failed to download %s", binary)
                            errors.append(
                                "Failed to download %s: %s" % (binary, exc)
                            )
                        if errors:
                            return uploaded, errors
                        # Extract pattern (xml) files from the rpm
                        for xml in extract_rpm(lab.real_path(binary), lab.path,
                                               ["*.xml"]):
                            meta = os.path.basename(xml)
                            submetatype = os.path.basename(
                                os.path.dirname(xml)
                            )
                            self.log.debug(
                                "%s %s %s", meta, metatype, submetatype
                            )
                            try:
                                with open(lab.real_path(xml), 'r') as fd:
                                    metadata = [
                                        line.replace("@PROJECT@", project)
                                        for line in fd.readlines()
                                    ]
                                # Update meta
                                if submetatype == "aggregates":
                                    pkgname = os.path.splitext(meta)[0]
                                    core.edit_meta(
                                        metatype='pkg',
                                        path_args=(project, pkgname),
                                        template_args=({
                                            'name': pkgname,
                                            'user': 'cibot'
                                        }),
                                        apiurl=self.obs.apiurl
                                    )
                                    u = core.makeurl(
                                        self.obs.apiurl,
                                        ['source', project, pkgname,
                                         '_aggregate']
                                    )
                                    self.log.debug('URL: %s', u)
                                    self.log.debug('METADATA: %s', metadata)
                                    core.http_PUT(u, data="\n".join(metadata))
                                else:
                                    core.edit_meta(
                                        metatype, project,
                                        data=metadata,
                                        apiurl=self.obs.apiurl
                                    )
                                uploaded.append(metatype + '/' + meta)
                            except Exception as exc:
                                self.log.exception(
                                    "Failed to upload %s", meta
                                )
                                errors.append(
                                    "Failed to upload %s: %s" % (meta, exc)
                                )
                    return uploaded, errors
