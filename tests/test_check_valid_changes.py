import unittest

from mock import Mock

from check_valid_changes import Validator
from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_valid_changes"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock()
        ctrl.message = "start"
        self.participant.handle_lifecycle_control(ctrl)

    def test_handle_wi(self):
        # FIXME: for some reason creation of Validator instance is conditional
        #        hence create it here, not in setUp()
        self.participant.validator = Validator()

        wid = Mock()
        wid.fields.ev.actions = []
        wid.fields.msg = None
        wid.params.using = "relevant_changelog"
        fake_action = {
            "relevant_changelog": ["fake"]
        }
        wid.fields.ev.actions = [fake_action]

        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

        wid.fields.ev.actions = []
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        wid.params.using = "full"
        wid.fields.changelog = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

        fake_action = {
            "fake": "fake"
        }
        wid.fields.ev.actions = [fake_action]
        wid.fields.changelog = "*invalid"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)
        wid.fields.changelog = "* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1\n\n"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

if __name__ == '__main__':
    unittest.main()
