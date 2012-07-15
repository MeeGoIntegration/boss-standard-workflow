#!/usr/bin/python
"""Participant to select test binaries to execute for this build.

:term:'Workitem' fields IN:

:Parameters:
    qa.selected_packages:
       Names of all candidate test packages (Provides: qa-tests)
    qa.stage
       (optional) Name of promotion stage

:term:`Workitem` fields OUT:

:Returns:
    result(Boolean):
        True if everything was ok 
    qa.selected_packages(dictionary):
        Dictionary with filtered list of binary packages to use for testing and their requirements


"""

class ParticipantHandler(object):
    """Participant class as defined by the SkyNET API"""

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        pass


    def handle_wi(self, wid):
        """Actual work thread"""
        wid.result = False

        if wid.qa and wid.qa.selected_packages:
            binaries = wid.qa.selected_packages.as_dict()

            for binary, provides in binaries.items():
                print "%s %s" % ( binary, provides )
                if wid.fields.qa.stage:
                    if not "%s-%s" % ("qa-tests-requirement-stage-is", wid.fields.qa.stage) in provides:
                        del(binaries[binary])

            wid.qa.selected_packages = binaries

        wid.result = True

