#!/usr/bin/python
""" Updates package patterns for a specific project as per package-groups
package updates

:term:`Workitem` fields IN:

:Parameters:
   project(string):
      project of which to update patterns to

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if the update was successfull

"""
import subprocess as sub


from buildservice import BuildService


class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = None
        self.oscrc = None

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")

    def setup_obs(self, namespace):
        """ setup the Buildservice instance using the namespace as an alias
            to the apiurl """

        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    def get_rpm_file(self):
        project = "Project:DE:Trunk"
        target = "standard"
        package = "ce-groups"
        binaries = self.obs.getBinaryList(project, target, package)
        rpm_file = ""
        for bin in binaries:
            if not bin.endswith("src.rpm"):
                if bin.endswith("rpm"):
                    rpm_file = self.obs.getBinary(project, target, package, bin, "/tmp/")
        return rpm_file

    def extract_rpm(self, rpm_file):
        rpm2cpio_args = ['/usr/bin/rpm2cpio', rpm_file]
        cpio_args = ['/bin/cpio', '-idv']
        sub.check_call()

    def handle_wi(self, wid):
        """ actual job thread """
        f = wid.fields
        self.setup_obs(f.namespace)
        rpm_file = self.get_rpm_file()
        xmls = self.extract_rpm(rpm_file)

