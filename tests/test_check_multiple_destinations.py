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
        fake_action1 = {
            "targetproject": "fake1"
        }
        fake_action2 = {
            "targetproject": "fake2"
        }
        # test single destination project in one request
        wid.fields.ev.actions = [fake_action1]
        self.participant.handle_wi(wid)
        # test multiple destination projects one request
        wid.fields.ev.actions = [fake_action1, fake_action2]
        self.participant.handle_wi(wid)

        wid.fields.ev.actions = []
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)


if __name__ == '__main__':
    unittest.main()
