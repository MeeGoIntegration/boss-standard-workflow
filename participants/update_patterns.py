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
import os
from tempfile import TemporaryFile, \
                     mkdtemp


from buildservice import BuildService


class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = None
        self.oscrc = None
        self.tmp_dir = mkdtemp()

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
        """ Download ce-groups binary rpm and return path to it.
        """
        project = "Project:DE:Trunk"
        target = "standard"
        package = "ce-groups"
        binaries = self.obs.getBinaryList(project, target, package)
        rpm_file = ""
        for binary in binaries:
            if not binary.endswith("src.rpm"):
                if binary.endswith("rpm"):
                    rpm_file = self.obs.getBinary(project,
                                                  target,
                                                  package,
                                                  binary,
                                                  "/tmp/")
        return rpm_file

    def extract_rpm(self, rpm_file):
        """Extract RPM file and fetch all xml files it produced to an array.
        :Parameters
            rpm_file: path to rpm file
        """
        rpm2cpio_args = ['/usr/bin/rpm2cpio', rpm_file]
        cpio_args = ['/bin/cpio', '-idv']
        cpio_out = TemporaryFile(dir=self.tmp_dir)
        cpio_output = TemporaryFile(dir=self.tmp_dir)
        cpio_out.write(sub.check_output(rpm2cpio_args,
                                        cwd=self.tmp_dir))
        sub.check_call(cpio_args,
                       stdin=cpio_out,
                       stdout=cpio_output,
                       cwd=self.tmp_dir)
        cpio_out.close()
        xml_files = []
        for xml_line in cpio_output:
            if xml_line.endswith('.xml'):
                xml_files.append(self.tmp_dir + '/' + xml_line)
        cpio_output.close()

        return xml_files

    def handle_wi(self, wid):
        """ actual job thread """
        wid.result = False
        fields = wid.fields
        self.setup_obs(fields.namespace)
        project = wid.fields.project
        rpm_file = self.get_rpm_file()
        if rpm_file:
            xmls = self.extract_rpm(rpm_file)
            for xml in xmls:
                self.obs.setProjectPattern(project, xml)
        os.rmdir(self.tmp_dir)
        wid.result = True

