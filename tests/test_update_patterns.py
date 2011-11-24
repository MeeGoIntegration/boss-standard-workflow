"""Unittests for update_patterns participant."""

import unittest
from mock import Mock
import subprocess as sub
import os
import shutil
from StringIO import StringIO
from urllib2 import HTTPError

from common_test_lib import BaseTestParticipantHandler, DATADIR


OBS_FILES_GOOD = ["ce-groups-1.1-12.src.rpm", "README", "ce-groups-1.1-12.noarch.rpm"]
OBS_FILES_BAD = ["ce-groups-1.1-12.src.rpm", "ce-groups.changes"]
RPM_NAME = 'test-groups-0.1-1.noarch.rpm'

__module_setup__ = False

def setUpModule():
    global __module_setup__
    sub.check_call(['make','groupsrpm'],
            cwd=DATADIR, stdout=sub.PIPE, stderr=sub.PIPE)
    __module_setup__ = True

def tearDownModule():
    sub.check_call(['make','clean'],
            cwd=DATADIR, stdout=sub.PIPE, stderr=sub.PIPE)

def get_binary(project, target, package, binary, path):
    shutil.copy(os.path.join(DATADIR, RPM_NAME), path)


class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "update_patterns"

    def setUp(self):
        super(TestParticipantHandler, self).setUp()
        # setUpModule is not supported in Python 2.6 unittest, but it works on
        # later versions and when run with nose
        if not __module_setup__:
            setUpModule()

        self.wid = self.fake_workitem
        self.wid.params.project = "Project:Test"
        self.wid.fields.ev.namespace = "foo"
        self.wid.fields.patterns = {
                "test-groups":{
                    "test_repo/i586": [RPM_NAME]}}
        self.participant.obs.getBinary.side_effect = get_binary

    def tearDown(self):
        super(TestParticipantHandler, self).tearDown()
        if not __module_setup__:
            tearDownModule()


    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_normal(self):
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)

    def test_missing_project(self):
        self.wid.params.project = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)

    def test_missing_patterns(self):
        self.wid.fields.patterns = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)

    def test_binary_download_404(self):
        self.participant.obs.getBinary.side_effect = HTTPError(
                "http://fake_url", 404, "Not found", [],
                StringIO("File not found"))
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)
        self.assertEqual(len(self.wid.fields.msg), 1)
        self.assertTrue("http://fake_url" in self.wid.fields.msg[0])

    def test_binary_download_fail(self):
        self.participant.obs.getBinary.side_effect = Exception("DOWNLOAD FAIL")
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)
        self.assertEqual(len(self.wid.fields.msg), 1)
        self.assertTrue("DOWNLOAD FAIL" in self.wid.fields.msg[0])

    def test_no_patterns_in_package(self):
        self.participant.obs.getBinary = Mock()
        real_er = self.mut.extract_rpm
        self.mut.extract_rpm = Mock()
        self.mut.extract_rpm.return_value = []
        try:
            self.participant.handle_wi(self.wid)
            self.assertFalse(self.wid.result)
            print self.wid.dump()
            self.assertEqual(len(self.wid.fields.msg), 1)
            self.assertTrue("No patterns found" in self.wid.fields.msg[0])
        finally:
            self.mut.extract_rpm = real_er

    def test_pattern_update_400(self):
        self.participant.obs.setProjectPattern.side_effect = HTTPError(
                "http://fake_url", 400, "Bad Request", [],
                StringIO("Bad request description"))
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)
        self.assertEqual(len(self.wid.fields.msg), 1)
        self.assertTrue("http://fake_url" in self.wid.fields.msg[0])

    def test_pattern_update_fail(self):
        self.participant.obs.setProjectPattern.side_effect = \
                ValueError("bad bad bad")
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)
        self.assertEqual(len(self.wid.fields.msg), 1)
        self.assertTrue("bad bad bad" in self.wid.fields.msg[0])

if __name__ == "__main__":
    unittest.main()
