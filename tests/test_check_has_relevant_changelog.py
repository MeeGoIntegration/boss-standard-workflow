import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_has_relevant_changelog"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        self.participant.handle_lifecycle_control(None)

    def test_quality_check(self):
        wid = Mock()
        wid.fields.ev.actions = []
        wid.fields.msg = None
        self.assertRaises(RuntimeError, self.participant.quality_check, wid)

        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake"
        }
        wid.fields.ev.actions = [fake_action]

        self.participant.quality_check(wid)

    def test_handle_wi(self):
        wid = Mock()
        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake"
        }
        wid.fields.ev.actions = [fake_action]

        self.participant.handle_wi(wid)

if __name__ == '__main__':
    unittest.main()
