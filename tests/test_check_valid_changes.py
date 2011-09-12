import unittest

from mock import Mock

from check_valid_changes import Validator
from common_test_lib import BaseTestParticipantHandler
from RuoteAMQP.workitem import Workitem

BASE_WORKITEM = '{"fei": 1, "fields": { "params": {}, "ev": {} }}'

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_valid_changes"

    good_changelog = "* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1\n- made changes"
    bad_changelog = "* invalid"

    def setUp(self):
        BaseTestParticipantHandler.setUp(self)
        self.wid = Workitem(BASE_WORKITEM)

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock()
        ctrl.message = "start"
        self.participant.handle_lifecycle_control(ctrl)

    def test_empty_actions_ok(self):
        self.wid.params.using = "relevant_changelog"
        self.wid.fields.ev.actions = []
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)

    def test_missing_actions(self):
        self.wid.params.using = "relevant_changelog"
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)
        self.assertTrue("actions missing" in self.wid.fields.msg[-1])

    def test_missing_relevant_changelog(self):
        self.wid.params.using = "relevant_changelog"
        fake_action = {
            "sourcepackage": "mock"
        }
        self.wid.fields.ev.actions = [fake_action]
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)
        self.assertTrue("Missing relevant_changelog" in self.wid.fields.msg[-1])

    def test_missing_changelog(self):
        self.wid.params.using = "full"
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)
        self.assertTrue("changelog missing" in self.wid.fields.msg[-1])

    def test_unknown_mode(self):
        self.wid.params.using = "Ford Prefect"
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)
        self.assertTrue("Unknown mode" in self.wid.fields.msg[-1])

    def test_default_mode_full(self):
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)
        self.assertTrue("changelog missing" in self.wid.fields.msg[-1])

    def test_relevant_bad(self):
        self.wid.params.using = "relevant_changelog"
        fake_action = {
            "relevant_changelog": [self.bad_changelog]
        }
        self.wid.fields.ev.actions = [fake_action]
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)

    def test_relevant_good(self):
        self.wid.params.using = "relevant_changelog"
        fake_action = {
            "relevant_changelog": [self.good_changelog]
        }
        self.wid.fields.ev.actions = [fake_action]
        self.participant.handle_wi(self.wid)
        print self.wid.fields.msg
        self.assertTrue(self.wid.result)

    def test_full_bad(self):
        self.wid.params.using = "full"
        self.wid.fields.changelog = self.bad_changelog
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)

    def test_full_good(self):
        self.wid.params.using = "full"
        self.wid.fields.changelog = self.good_changelog
        self.participant.handle_wi(self.wid)
        print self.wid.fields.msg
        self.assertTrue(self.wid.result)

if __name__ == '__main__':
    unittest.main()
