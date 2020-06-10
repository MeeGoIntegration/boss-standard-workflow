import unittest

from mock import Mock
from RuoteAMQP import Workitem

from common_test_lib import BaseTestParticipantHandler, WI_TEMPLATE

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_has_relevant_changelog"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        self.participant.handle_lifecycle_control(None)

    def test_quality_check(self):
        wid = Workitem(WI_TEMPLATE)
        wid.fields.ev.actions = []
        wid.fields.msg = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

        wid.fields.ev.actions = self.fake_actions

        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

        for action in wid.fields.ev.actions:
            if action["type"] == "submit":
                action["relevant_changelog"] = "Something"
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

        for action in wid.fields.ev.actions:
            if action["type"] == "submit":
                action["relevant_changelog"] = "Something\xe1\xe1"
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

if __name__ == '__main__':
    unittest.main()
