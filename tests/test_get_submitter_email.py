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
        wid = Mock()
        wid.fields.msg = None
        wid.fields.email = None
        wid.fields.ev.who = "somebody"

        self.participant.quality_check(wid)
        self.assertFalse(wid.result)

        self.participant.obs.getUserEmail.return_value = "some email"
        self.participant.quality_check(wid)
        self.assertTrue(wid.result)

        wid.fields.ev.who = ""
        self.assertRaises(RuntimeError, self.participant.quality_check, wid)

    def test_handle_wi(self):
        wid = Mock()
        self.participant.handle_wi(wid)

if __name__ == '__main__':
    unittest.main()
