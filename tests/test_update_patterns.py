'''
Created on Sep 21, 2011

@author: locusfwork
'''
import unittest
from mock import Mock
import subprocess as sub
import os
import shutil
from StringIO import StringIO
from tempfile import mkdtemp
from urllib2 import HTTPError

from common_test_lib import BaseTestParticipantHandler, DATADIR


OBS_FILES_GOOD = ["ce-groups-1.1-12.src.rpm", "README", "ce-groups-1.1-12.noarch.rpm"]
OBS_FILES_BAD = ["ce-groups-1.1-12.src.rpm", "ce-groups.changes"]
RPM_NAME = 'test-groups-0.1-1.noarch.rpm'


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

class TestParticipant(TestParticipantHandler):
    """Tests for individual methods, not through handle_wi"""

    def setUp(self):
        TestParticipantHandler.setUp(self)
        self.participant.tmp_dir = mkdtemp()

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_extract_patterns(self):
        sub.check_call(['make','groupsrpm'],
                       cwd=DATADIR, stdout=sub.PIPE, stderr=sub.PIPE)
        shutil.copy(os.path.abspath(os.path.join(DATADIR,RPM_NAME)),
                    self.participant.tmp_dir + '/')

        xml_files = self.participant.extract_patterns(os.path.join(
                                                 self.participant.tmp_dir,
                                                 'test-groups-0.1-1.noarch.rpm'
                                                 ))
        self.assertTrue(len(xml_files)>=1)
        for xml_file in xml_files:
            self.assertTrue(xml_file.endswith('.xml'))
            self.assertTrue(os.path.exists(xml_file))

        sub.check_call(['make','clean'],
                       cwd=DATADIR, stdout=sub.PIPE, stderr=sub.PIPE)

    def test_get_rpm_file(self):
        self.obs.getBinaryList.return_value = OBS_FILES_GOOD
        self.obs.getBinary.return_value = "ce-groups-1.1-12.noarch.rpm"
        rpmfile = self.participant.get_rpm_file(
            self.obs, 'Project:Foo', 'standard/i586', 'ce-groups')
        self.assertTrue(rpmfile)
        self.assertTrue(rpmfile.endswith('.rpm'))
        self.assertFalse(rpmfile.endswith('.src.rpm'))

    def test_missing_rpm(self):
        self.obs.getBinaryList.return_value = OBS_FILES_BAD
        self.obs.getBinary.return_value = ""
        self.assertRaises(RuntimeError,
                          self.participant.get_rpm_file,
                          self.obs, 'Project:Foo', 'standard/i586', 'ce-groups')


class TestHandleWi(TestParticipantHandler):

    def setUp(self):
        TestParticipantHandler.setUp(self)
        sub.check_call(['make','groupsrpm'],
                       cwd=DATADIR, stdout=sub.PIPE, stderr=sub.PIPE)

        self.wid = self.fake_workitem
        self.wid.params.project = "Project:Test"
        self.wid.fields.ev.namespace = "foo"

        self.participant.get_rpm_file = Mock()
        self.participant.get_rpm_file.return_value = \
            os.path.abspath(os.path.join(DATADIR, RPM_NAME))

        self.obs.getProjectRepositories.return_value = ['standard']
        self.obs.getRepositoryArchs.return_value = ['i586']

    def tearDown(self):
        TestParticipantHandler.tearDown(self)
        sub.check_call(['make','clean'],
                       cwd=DATADIR, stdout=sub.PIPE, stderr=sub.PIPE)

    def test_normal(self):
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)

    def test_missing_project(self):
        self.wid.params.project = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)

    def test_missing_repository(self):
        self.obs.getProjectRepositories.return_value = []
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)

    def test_param_repository(self):
        self.wid.params.repository = 'nonstandard'
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)
        self.assertEqual(self.obs.getProjectRepositories.call_count, 0)
        self.assertEqual(self.participant.get_rpm_file.call_args[0][2],
                         'nonstandard/i586')

    def test_param_arch(self):
        self.wid.params.arch = 'ppc'
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)
        self.assertEqual(self.obs.getRepositoryArchs.call_count, 0)
        self.assertEqual(self.participant.get_rpm_file.call_args[0][2],
                         'standard/ppc')

    def test_bad_request(self):
        self.obs.setProjectPattern.side_effect = \
            HTTPError("fake_url", 400, "Bad Request", [],
                      StringIO("Bad request description"))
        self.assertRaises(HTTPError, self.participant.handle_wi, self.wid)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
