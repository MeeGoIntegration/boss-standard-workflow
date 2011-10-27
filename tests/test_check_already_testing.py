import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_already_testing"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_setup_obs(self):
        self.participant.setup_obs("test_namespace")

    def test_handle_wi(self):
        wid = self.fake_workitem
        wid.fields.ev.rid = 1
        wid.fields.test_project = "fake"
        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "targetpackage": "fake"
        }
        wid.fields.ev.actions = [fake_action]
        wid.fields.msg = None

        self.participant.handle_wi(wid)

        self.participant.obs.hasChanges.return_value = False
        self.participant.handle_wi(wid)

        wid.fields.ev.rid = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

if __name__ == '__main__':
    unittest.main()
