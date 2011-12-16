import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler


class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "is_repo_published"

    def setUp(self):
        super(TestParticipantHandler, self).setUp()
        self.fake_workitem.fields.ev.namespace = "test"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_repos_not_published(self):
        wid = self.fake_workitem
        wid.params.project = "fake_project"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_repos_published(self):
        self.participant.obs.getRepoState.return_value.update({
                "fake_repo_1/i586": "published",
                "fake_repo_3/armv8el": "published"})
        self.participant.handle_wi(self.fake_workitem)
        self.assertTrue(self.fake_workitem.result)

    def test_disabled(self):
        self.participant.obs.getRepoState.return_value.update({
                "fake_repo_1/i586": "published",
                "fake_repo_3/armv8el": "unpublished"})
        self.participant.handle_wi(self.fake_workitem)
        self.assertTrue(self.fake_workitem.result)

    def test_specific_repo(self):
        self.fake_workitem.params.repository = "fake_repo_2"
        self.participant.handle_wi(self.fake_workitem)
        self.assertTrue(self.fake_workitem.result)

    def test_specific_arch(self):
        self.fake_workitem.params.arch = "armv7el"
        self.participant.handle_wi(self.fake_workitem)
        self.assertTrue(self.fake_workitem.result)


if __name__ == '__main__':
    unittest.main()
