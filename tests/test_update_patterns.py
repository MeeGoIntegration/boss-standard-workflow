'''
Created on Sep 21, 2011

@author: locusfwork
'''
import unittest
from mock import Mock
import subprocess as sub
import os
import shutil
from tempfile import mkdtemp

from common_test_lib import BaseTestParticipantHandler


OBS_FILES_GOOD = ["ce-groups-1.1-12.src.rpm", "README", "ce-groups-1.1-12.noarch.rpm"]
OBS_FILES_BAD = ["ce-groups-1.1-12.src.rpm", "ce-groups.changes"]
RPM_NAME = 'test-groups-0.1-1.noarch.rpm'
DATA = os.path.join(os.path.dirname(__file__), "test_data")


class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "update_patterns"

    def setUp(self):
        BaseTestParticipantHandler.setUp(self)
        # obs is not an attribute of the participant in update_patterns
        self.obs = self.participant.obs
        del self.participant.obs

    def tearDown(self):
        BaseTestParticipantHandler.tearDown(self)
        if self.participant.tmp_dir:
            shutil.rmtree(self.participant.tmp_dir)

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_handle_wi(self):
        sub.check_call(['make','groupsrpm'],
                       cwd=DATA, stdout=sub.PIPE, stderr=sub.PIPE)

        wid = self.fake_workitem
        wid.params.project = "Project:Test"
        wid.fields.ev.namespace = "foo"

        self.participant.get_rpm_file = Mock()
        self.participant.get_rpm_file.return_value = \
            os.path.abspath(os.path.join(DATA, RPM_NAME))

        self.obs.getProjectRepositories.return_value = ['standard']
        self.participant.handle_wi(wid)

        sub.check_call(['make','clean'],
                       cwd=DATA, stdout=sub.PIPE, stderr=sub.PIPE)

    def test_extract_rpm(self):
        self.participant.tmp_dir = mkdtemp()
        sub.check_call(['make','groupsrpm'],
                       cwd=DATA, stdout=sub.PIPE, stderr=sub.PIPE)
        shutil.copy(os.path.abspath(os.path.join(DATA,RPM_NAME)),
                    self.participant.tmp_dir + '/')

        xml_files = self.participant.extract_rpm(os.path.join(
                                                 self.participant.tmp_dir,
                                                 'test-groups-0.1-1.noarch.rpm'
                                                 ))
        self.assertTrue(len(xml_files)>=1)
        for xml_file in xml_files:
            self.assertTrue(xml_file.endswith('.xml'))

        sub.check_call(['make','clean'],
                       cwd=DATA, stdout=sub.PIPE, stderr=sub.PIPE)

    def test_get_rpm_file(self):
        self.participant.tmp_dir = mkdtemp()
        self.obs.getBinaryList.return_value = OBS_FILES_GOOD
        self.obs.getBinary.return_value = "ce-groups-1.1-12.noarch.rpm"
        rpmfile = self.participant.get_rpm_file(
            self.obs, 'ce-groups', 'Project:Foo', 'i386')
        self.assertTrue(rpmfile)
        self.assertTrue(rpmfile.endswith('.rpm'))
        self.assertFalse(rpmfile.endswith('.src.rpm'))

    def test_missing_rpm(self):
        self.participant.tmp_dir = mkdtemp()
        self.obs.getBinaryList.return_value = OBS_FILES_BAD
        self.obs.getBinary.return_value = ""
        self.assertRaises(RuntimeError,
                          self.participant.get_rpm_file,
                          self.obs, 'ce-groups', 'Project:Foo', 'i386')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
