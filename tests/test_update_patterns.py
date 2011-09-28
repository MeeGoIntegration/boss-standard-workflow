'''
Created on Sep 21, 2011

@author: locusfwork
'''
import unittest
from mock import Mock
import subprocess as sub
import os

from common_test_lib import BaseTestParticipantHandler

OBS_FILES_GOOD = ["ce-groups-1.1-12.src.rpm", "README", "ce-groups-1.1-12.noarch.rpm"]
OBS_FILES_BAD = []

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "update_patterns"

    def setUp(self):
        BaseTestParticipantHandler.setUp(self)
        sub = Mock()
        sub.check_call = Mock()

    def tearDown(self):
        BaseTestParticipantHandler.tearDown(self)

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_setup_obs(self):
        self.participant.setup_obs("test_namespace")

    def test_handle_wi(self):
        sub.check_call(['make','groupsrpm'],
                       cwd=os.path.abspath('./tests/test_data'),
                       stdout=sub.PIPE,
                       stderr=sub.PIPE)

        wid = Mock()
        wid.fields.project = "Project:Test"
        wid.fields.namespace = "foo"
        self.participant.obs.getBinaryList.return_value = OBS_FILES_BAD
        self.assertRaises(RuntimeError, self.participant.handle_wi,wid)
        self.participant.obs.getBinaryList.return_value = OBS_FILES_GOOD
        self.participant.get_rpm_file = Mock()
        self.participant.get_rpm_file.return_value = './tests/test_data/test-groups-0.1-1.noarch.rpm'
        self.participant.handle_wi(wid)

        sub.check_call(['make','clean'],
                       cwd=os.path.abspath('./tests/test_data'),
                       stdout=sub.PIPE,
                       stderr=sub.PIPE)

    def test_extract_rpm(self):
        sub.check_call(['make','groupsrpm'],
                       cwd='./tests/test_data',
                       stdout=sub.PIPE,
                       stderr=sub.PIPE)

        xml_files = self.participant.extract_rpm('./tests/test_data/test-groups-0.1-1.noarch.rpm')
        self.assertTrue(len(xml_files)>=1)
        for xml_file in xml_files:
            self.assertTrue(xml_file.endswith('.xml'))

        sub.check_call(['make','clean'],
                       cwd='./tests/test_data',
                       stdout=sub.PIPE,
                       stderr=sub.PIPE)

    def test_get_rpm_file(self):
        self.participant.obs.getBinaryList.return_value = OBS_FILES_GOOD
        self.participant.obs.getBinary.return_value = "ce-groups-1.1-12.noarch.rpm"
        rpmfile = self.participant.get_rpm_file('ce-groups',
                                                'Project:Foo',
                                                'i386')
        self.assertTrue(rpmfile)
        self.assertTrue(rpmfile != "")
        self.assertTrue(rpmfile.endswith('.rpm'))
        self.assertFalse(rpmfile.endswith('.src.rpm'))

        self.participant.obs.getBinaryList.return_value = OBS_FILES_BAD
        self.participant.obs.getBinary.return_value = ""
        self.assertRaises(RuntimeError,
                          self.participant.get_rpm_file,
                          'ce-groups',
                          'Project:Foo',
                          'i386')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
