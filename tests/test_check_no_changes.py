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

    def mock_has_changes(self, *args, **kwargs):
        """Return True for the first call, False after that."""
        self.has_changes_call_count += 1
        return self.has_changes_call_count == 1

    def test_handle_wi(self):
        wid = self.fake_workitem
        wid.fields.ev.namespace = "test"
        wid.fields.ev.actions = self.fake_actions
        wid.fields.msg = None

        self.participant.obs.hasChanges.return_value = True
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

        self.participant.obs.hasChanges.return_value = False
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

        self.participant.obs.hasChanges.side_effect = self.mock_has_changes
        self.has_changes_call_count = 0
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_handle_missing_fields(self):
        wid = self.fake_workitem
        wid.fields.ev = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

        wid.fields.ev = {}
        wid.fields.ev.namespace = "namespace"
        wid.fields.ev.actions = []
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

        wid.fields.ev.namespace = None
        wid.fields.ev.actions = self.fake_actions
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)


if __name__ == '__main__':
    unittest.main()
