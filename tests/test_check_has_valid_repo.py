import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler, BuildServiceFakeRepos


class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_has_valid_repo"

    def setUp(self):
        super(TestParticipantHandler, self).setUp()
        self.fake_workitem.fields.ev.namespace = "test"
        self.fake_workitem.fields.ev.actions = self.fake_actions

        repos = BuildServiceFakeRepos(self.participant.obs)
        repos.repo = self.repo = {
            "fake_target": ["repo"],
            "fake_source": ["repo"],
            }
        repos.arch = self.arch = {
            "fake_target/repo":["i586"],
            "fake_source/repo":["i586"],
            }
        repos.path = self.path = {
            "fake_target/repo":[],
            "fake_source/repo":["fake_target/repo"],
            }


    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_no_actions(self):
        wid = self.fake_workitem
        wid.fields.ev.actions = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        wid.fields.ev = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

    def test_no_source_repos(self):
        wid = self.fake_workitem
        self.repo["fake_source"] = []

        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_valid_repos(self):
        wid = self.fake_workitem
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

    def test_invalid_repos(self):
        wid = self.fake_workitem
        self.repo["fake_source"] = []
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_invalid_arch(self):
        wid = self.fake_workitem
        self.arch["fake_source/repo"] = ["i386"]
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_bad_build_target(self):
        wid = self.fake_workitem
        self.path["fake_source/repo"] = ["something/else"]
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_no_build_target(self):
        wid = self.fake_workitem
        self.path["fake_source/repo"] = []
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_bad_project(self):
        wid = self.fake_workitem
        for action in wid.fields.ev.actions:
            action["sourceproject"] = "invalid"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_publishing_disabled(self):
        wid = self.fake_workitem
        self.participant.obs.getRepoState.return_value = {
                "repo/i586": "unpublished"}
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)


if __name__ == '__main__':
    unittest.main()
