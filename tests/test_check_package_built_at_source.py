import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler, BuildServiceFakeRepos

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_package_built_at_source"

    def setUp(self):
        super(TestParticipantHandler, self).setUp()
        self.fake_action = {
            "type" : "submit",
            "sourceproject": "source",
            "sourcepackage": "fake",
            "targetproject": "target"
        }
        self.fake_workitem.fields.ev.actions = [self.fake_action]
        self.fake_workitem.fields.ev.namespace = "test"

        repos = BuildServiceFakeRepos(self.participant.obs)
        repos.repo = self.repo = {
            "target": ["repo"],
            "source": ["repo"],
            }
        repos.arch = self.arch = {
            "target/repo":["i586"],
            "source/repo":["i586"],
            }
        repos.path = self.path = {
            "target/repo":[],
            "source/repo":["target/repo"],
            }

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_success(self):
        wid = self.fake_workitem
        self.participant.obs.getPackageStatus.return_value = {
                "repo/i586":"succeeded"}
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)
        self.assertEqual(len(wid.fields.msg), 0)

    def test_failure(self):
        wid = self.fake_workitem
        self.participant.obs.getPackageStatus.return_value = {
                "repo/i586":"failed"}
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)
        self.assertEqual(len(wid.fields.msg), 1)

    def test_excluded(self):
        wid = self.fake_workitem
        self.participant.obs.getPackageStatus.return_value = {
                "repo/i586": "excluded"}
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)
        self.assertEqual(len(wid.fields.msg), 1)

    def test_other_status(self):
        wid = self.fake_workitem
        self.participant.obs.getPackageStatus.return_value = {
                "repo/i586": "somethingelse"}
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)
        self.assertEqual(len(wid.fields.msg), 1)

    def test_bad_project(self):
        wid = self.fake_workitem
        self.fake_action["sourceproject"] = "invalid"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)
        self.assertEqual(len(wid.fields.msg), 1)

    def test_missing_target(self):
        wid = self.fake_workitem
        self.path["source/repo"] = []
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)
        self.assertEqual(len(wid.fields.msg), 1)

    def test_extra_arch(self):
        wid = self.fake_workitem
        self.arch["source/repo"].append("arm")
        self.participant.obs.getPackageStatus.return_value = {
                "repo/i586":"succeeded",
                "repo/arm":"failed"}
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)
        self.assertEqual(len(wid.fields.msg), 0)

    def test_params(self):
        wid = self.fake_workitem
        wid.fields.msg = None
        self.fake_workitem.fields.ev.namespace = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.fake_workitem.fields.ev.namespace = "test"
        wid.fields.ev.actions = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)



if __name__ == '__main__':
    unittest.main()
