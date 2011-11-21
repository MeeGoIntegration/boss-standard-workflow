import unittest

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_multiple_destinations"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        self.participant.handle_lifecycle_control(None)

    def test_handle_wi(self):
        wid = self.fake_workitem
        wid.fields.msg = None
        # test single destination project in one request
        wid.fields.ev.actions = self.fake_actions
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

        # test multiple destination projects one request
        wid.fields.ev.actions[-1]["targetproject"] += "_other"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

        wid.fields.ev.actions = []
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)


if __name__ == '__main__':
    unittest.main()
