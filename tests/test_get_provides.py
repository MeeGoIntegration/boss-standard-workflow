"""Unittests for get_provides participant."""

import unittest
from mock import Mock

from common_test_lib import BaseTestParticipantHandler, BuildServiceFakeRepos


class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "get_provides"

    def setUp(self):
        super(TestParticipantHandler, self).setUp()
        self.fake_workitem.params.project = "project"
        self.fake_workitem.params.provide = "test"
        self.fake_workitem.fields.ev.namespace = "test"

        self.repos = BuildServiceFakeRepos(self.participant.obs)
        self.participant.obs.getPackageList.return_value = ["test"]
        self.participant.obs.getBinaryList.return_value = ["test-0.1-1.i586.rpm",
                "test-0.1-1.src.rpm"]
        self.participant.obs.getBinaryInfo.return_value = {
                'arch': 'i586',
                'description': 'Test package.',
                'mtime': '1322062515',
                'name': 'test',
                'provides': ['test = 0.1-1',
                             'test(x86-32) = 0.1-1'],
                'release': '1',
                'size': '3251',
                'summary': 'My test package',
                'version': '0.1'}


    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_normal(self):
        wid = self.fake_workitem
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)
        result = wid.fields.provides.as_dict()
        self.assertEqual(result["test"]["repo/i586"][0], "test-0.1-1.i586.rpm")

    def test_missing_param_project(self):
        wid = self.fake_workitem
        wid.params.project = None
        exc = self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.assertTrue("project" in str(exc))

    def test_bad_param_project(self):
        wid = self.fake_workitem
        wid.params.project = "foobear"
        exc = self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.assertTrue("Project not found" in str(exc))

    def test_missing_param_provide(self):
        wid = self.fake_workitem
        wid.params.provide = None
        exc = self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.assertTrue("provide" in str(exc))

    def test_param_field(self):
        wid = self.fake_workitem
        wid.params.field = "test"
        self.participant.handle_wi(wid)
        self.assertEqual(wid.fields.provides, None)
        result = wid.fields.test.as_dict()
        self.assertEqual(result["test"]["repo/i586"][0], "test-0.1-1.i586.rpm")

    def test_param_repository(self):
        wid = self.fake_workitem
        wid.params.repository = "repo"
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)
        result = wid.fields.provides.as_dict()
        self.assertEqual(result["test"]["repo/i586"][0], "test-0.1-1.i586.rpm")

    def test_bad_param_repository(self):
        wid = self.fake_workitem
        wid.params.repository = "badrepo"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_param_arch(self):
        wid = self.fake_workitem
        wid.params.arch = "i586"
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)
        result = wid.fields.provides.as_dict()
        self.assertEqual(result["test"]["repo/i586"][0], "test-0.1-1.i586.rpm")

    def test_param_arch(self):
        wid = self.fake_workitem
        wid.params.arch = "arm"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_param_repository_and_bad_arch(self):
        wid = self.fake_workitem
        wid.params.repository = "repo"
        wid.params.arch = "arm"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_source_skip(self):
        wid = self.fake_workitem
        self.participant.obs.getBinaryInfo.return_value["arch"] = "src"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

if __name__ == "__main__":
    unittest.main()
