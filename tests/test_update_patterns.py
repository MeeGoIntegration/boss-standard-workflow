'''
Created on Sep 21, 2011

@author: locusfwork
'''
import unittest
from mock import Mock

from common_test_lib import BaseTestParticipantHandler

OBS_FILES = ["ce-groups-1.1-12.src.rpm", "README", "ce-groups-1.1-12.noarch.rpm"]

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "update_patterns"

    def setUp(self):
        BaseTestParticipantHandler.setUp(self)
        self.participant.obs.getBinaryList.return_value = OBS_FILES
        self.participant.obs.getBinary.return_value = "ce-groups-1.1-12.noarch.rpm"
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
        wid = Mock()
        wid.fields.project = "Project:Test"
        wid.fields.namespace = "foo"
        self.participant.handle_wi(wid)

    def test_get_rpm_file(self):

        rpmfile = self.participant.get_rpm_file()
        self.assertIsNotNone(rpmfile)
        self.assertTrue(rpmfile != "")
        self.assertTrue(rpmfile.endswith('.rpm'))
        self.assertFalse(rpmfile.endswith('.src.rpm'))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
