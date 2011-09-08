import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_no_changes"

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
        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "targetproject": "fake",
            "targetpackage": "fake"
        }
        wid.fields.ev.actions = [fake_action]
        wid.fields.msg = None

        self.participant.quality_check(wid)

        self.participant.obs.hasChanges.return_value = True
        self.participant.quality_check(wid)

        self.participant.obs.hasChanges.return_value = False
        self.participant.quality_check(wid)

        wid.fields.ev.actions = []
        self.assertRaises(RuntimeError, self.participant.quality_check, wid)

    def test_handle_wi(self):
        wid = Mock()
        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "targetproject": "fake",
            "targetpackage": "fake"
        }
        wid.fields.ev.actions = [fake_action]

        self.participant.handle_wi(wid)

if __name__ == '__main__':
    unittest.main()
