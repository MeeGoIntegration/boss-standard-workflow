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
   ev.namespace(string):
      Namespace to use, see here:
      http://wiki.meego.com/Release_Infrastructure/BOSS/OBS_Event_List

:term:'Workitem' params IN:
   project(string)
       Project to update patterns to (and take groups package from)
   repository(string)
       Repository to take groups package from
       Default is to just pick one
   groups_package(string):
      Specifies the groups package to use for pattern providing package.
      Default is "package-groups"

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

    def get_rpm_file(self, obs, project, repository, package):
        """Download ce-groups binary rpm and return path to it.
        :Parameters
            project(string):
                Project to use.
            repository(string):
                Repository to download from.
            package(string):
                Name of the package to be downloaded from project repository.
        """
        print "Looking for %s in %s %s" % (package, project, repository)
        for binary in obs.getBinaryList(project, repository, package):
            if binary.endswith(".rpm") and not binary.endswith(".src.rpm"):
                return obs.getBinary(project, repository, package,
                                     binary, self.tmp_dir)
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
        obs = BuildService(oscrc=self.oscrc, apiurl=wid.fields.ev.namespace)
        project = wid.params.project
        repository = wid.params.repository
        package = wid.params.groups_package or "package-groups"
        if not project:
            raise RuntimeError("Missing mandatory parameter: project")
        if not repository:
            try:
                repository = obs.getProjectRepositories(project)[0]
            except IndexError:
                wid.error = "Target project %s has no repositories," \
                            " cannot get %s package" % (project, package)
                raise RuntimeError(wid.error)

        try:
            rpm_file = self.get_rpm_file(obs, project, repository, package)
            for xml in self.extract_rpm(rpm_file):
                obs.setProjectPattern(project, xml)
        finally:
            if os.path.exists(self.tmp_dir):
                shutil.rmtree(self.tmp_dir)

        wid.result = True
