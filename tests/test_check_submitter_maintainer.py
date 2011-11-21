import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_submitter_maintainer"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_setup_obs(self):
        self.participant.setup_obs("test_namespace")

    def test_quality_check(self):
        wid = self.fake_workitem
        wid.fields.ev.actions = self.fake_actions
        wid.fields.msg = None

        self.participant.handle_wi(wid)

        self.participant.obs.isMaintainer.return_value = True
        self.participant.handle_wi(wid)

        wid.fields.ev.actions = []
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)


if __name__ == '__main__':
    unittest.main()
