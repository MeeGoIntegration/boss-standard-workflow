#!/usr/bin/python
"""Participant to select test binaries to execute for this build.

:term:'Workitem' fields IN:

:Parameters:
    ev.namespace(string):
        Namespace to use, see here:
        http://wiki.meego.com/Release_Infrastructure/BOSS/OBS_Event_List
    test_packages:
       Names of all candidate test packages (Provides: qa-tests)
    qa.stage
       Name of promotion stage

:term:`Workitem` fields OUT:

:Returns:
    result(Boolean):
        True if providing binaries were found
    qa.selected_test_packages(dictionary):
        Dictionary with list of binary packages to use for testing and their requirements


"""

from collections import defaultdict
from urllib2 import HTTPError
from buildservice import BuildService


class ParticipantHandler(object):
    """Participant class as defined by the SkyNET API"""

    def handle_wi_control(self, ctrl):
        """Job control thread."""
        pass

    def handle_lifecycle_control(self, ctrl):
        """Participant control thread."""
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")


    def handle_wi(self, wid):
        """Actual work thread"""
        wid.result = False

        if wid.fields.debug_dump or wid.params.debug_dump: print wid.dump()

        self.obs = BuildService(oscrc=self.oscrc, apiurl=wid.fields.ev.namespace)

        project = wid.params.project
        packages = wid.fields.test_packages

        result = self.__get_provides(project, packages)

        test_packages = {}

        for package, binaries in result.items():
            for binary, provides in binaries.items():
                print provides
                if wid.fields.qa.stage and "%s-%s" % ("qa-tests-requirement-stage-is", wid.fields.qa.stage) in provides:
                    requirements = [ provide for provide in provides if provide.startswith("qa-tests-requirement") ]
                    test_packages[binary] = requirements

        wid.fields.qa.selected_test_packages = test_packages
        wid.result = True

    def __get_provides(self, project, packages, target):
        """Fetch the providing binary info."""
        result = {}
        for package in packages:
            for target, binaries in package.items():
                result[package] = defaultdict(list)
                for binary in binaries:
                    bininfo = self.obs.getBinaryInfo(project, target, package,
                                                     binary)
                    if bininfo.get("arch", "src") == "src":
                        continue
                    for name in bininfo.get("provides", []):
                        prov_name = name.split("=")[0].strip()
                        if prov_name not in result[package][binary]:
                            result[package][binary].append(prov_name)
        return result
