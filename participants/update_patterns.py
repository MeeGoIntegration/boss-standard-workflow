#!/usr/bin/python
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
   ev.project(string):
      project of which to update patterns to
   ev.namespace(string):
      Namespace to use, see here:
      http://wiki.meego.com/Release_Infrastructure/BOSS/OBS_Event_List
   ev.repo(string):
      Repository target to use

:term:'Workitem' params IN:
   groups_package_name(string):
      Specifies the groups package to use for pattern providing package.

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if the update was successfull

"""
import subprocess as sub
import os
import shutil
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

    def get_rpm_file(self, groups_package, project, target):
        """Download ce-groups binary rpm and return path to it.
        :Parameters
            groups_package(string):
                A package to be downloaded from project repository.
            project(string):
                Project to use.
            target(string):
                Target to download from.
        """
        for binary in self.obs.getBinaryList(project, target, groups_package):
            if not binary.endswith(".src.rpm") and binary.endswith(".rpm"):
                return self.obs.getBinary(project,
                                                  target,
                                                  groups_package,
                                                  binary,
                                                  self.tmp_dir)
        raise RuntimeError("Could not find an RPM file to download!")

    def extract_rpm(self, rpm_file):
        """Extract RPM file and fetch all xml files it produced to an array.
        :Parameters
            rpm_file: path to rpm file
        """
        rpm2cpio_args = ['/usr/bin/rpm2cpio', rpm_file]
        cpio_args = ['/bin/cpio', '-idv']
        cpio_archive = TemporaryFile(dir=self.tmp_dir)
        cpio_listing = TemporaryFile(dir=self.tmp_dir)
        sub.call(rpm2cpio_args,
                       cwd=self.tmp_dir,
                       stdout=cpio_archive)
        cpio_archive.seek(0)
        #print cpio_archive.read()
        sub.call(cpio_args,
                       stdin=cpio_archive,
                       stderr=cpio_listing,
                       cwd=self.tmp_dir)
        cpio_listing.seek(0)
        xml_files = []
        for xml_line in cpio_listing.readlines():
            xml_line = xml_line.strip()
            if xml_line.endswith('.xml'):
                xml_files.append(os.path.join(self.tmp_dir, xml_line))
        cpio_archive.close()
        cpio_listing.close()

        return xml_files

    def handle_wi(self, wid):
        """ actual job thread """
        wid.result = False
        fields = wid.fields
        self.setup_obs(fields.ev.namespace)
        project = wid.fields.ev.project
        target = wid.fields.ev.repo
        package = wid.params.group_package_name
        try:
            rpm_file = self.get_rpm_file(package,
                                         project,
                                         target)
            if rpm_file:
                xmls = self.extract_rpm(rpm_file)
                for xml in xmls:
                    self.obs.setProjectPattern(project, xml)
            wid.result = True
        finally:
            if os.path.exists(self.tmp_dir):
                shutil.rmtree(self.tmp_dir)
