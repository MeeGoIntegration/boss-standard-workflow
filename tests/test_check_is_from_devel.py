import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_is_from_devel"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        self.participant.handle_lifecycle_control(None)

    def test_quality_check(self):
        wid = Mock()
        fake_action = {
            "sourceproject": "fake"
        }
        wid.fields.ev.actions = [fake_action]
        wid.fields.msg = None

        wid.params.regexp = "fake_regexp"
        self.participant.quality_check(wid)

        wid.params.regexp = None
        self.assertRaises(RuntimeError, self.participant.quality_check, wid)

    def test_handle_wi(self):
        wid = Mock()
        fake_action = {
            "sourceproject": "fake"
        }
        wid.fields.ev.actions = [fake_action]
        wid.params.regexp = "fake_regexp"

        self.participant.handle_wi(wid)

if __name__ == '__main__':
    unittest.main()
