import unittest

from mock import Mock
from RuoteAMQP import Workitem

from common_test_lib import BaseTestParticipantHandler, WI_TEMPLATE

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_is_from_devel"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        self.participant.handle_lifecycle_control(None)

    def test_handle_wi(self):
        wid = Workitem(WI_TEMPLATE)
        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "type": "submit"
        }
        wid.fields.ev.actions = [fake_action]
        wid.fields.msg = None

        wid.params.regexp = "fake_regexp"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

        wid.params.regexp = "fake"
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

        wid.params.regexp = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

if __name__ == '__main__':
    unittest.main()
