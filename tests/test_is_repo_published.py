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



if __name__ == '__main__':
    unittest.main()
