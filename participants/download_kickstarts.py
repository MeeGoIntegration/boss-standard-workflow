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
    ev.project:
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

class ParticipantHandler(BuildServiceParticipant, RepositoryMixin):
    """Participant class as defined by the SkyNET API."""

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        if ctrl.message == "start":
            if ctrl.config.has_option("download_kickstarts", "storage"):
                self.basepath = ctrl.config.get("download_kickstarts",
                        "storage")
            else:
                raise RuntimeError("Missing mandatory config option "
                        "[download_kickstarts] storage")

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wid):
        """Job thread."""
        wid.result = False
        if not wid.params.conf_package:
            raise RuntimeError("Mandatory parameter 'conf_package' missing")
        if not wid.fields.ev or not wid.fields.ev.project:
            raise RuntimeError("Mandatory field 'ev.project' missing")

        # Use given subdirectory or use workflowid
        # TODO: Maybe support some substitutions in the path parameter
        path = wid.params.path or wid.wfid

        # Find the package

        # Find RPMs

        # Extract RPMs in temporary dir

        # Move kickstarts to storage
