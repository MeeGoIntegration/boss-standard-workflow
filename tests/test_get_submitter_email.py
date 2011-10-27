import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "get_submitter_email"

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
        wid.fields.msg = None
        wid.fields.mail_to = None
        wid.fields.ev.who = "somebody"

        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

        self.participant.obs.getUserEmail.return_value = "some email"
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

        wid.fields.ev.who = ""
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

    def test_handle_wi(self):
        wid = Mock()


if __name__ == '__main__':
    unittest.main()
