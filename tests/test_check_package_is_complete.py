import unittest

from mock import Mock
from RuoteAMQP import Workitem

from common_test_lib import BaseTestParticipantHandler, WI_TEMPLATE

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_package_is_complete"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_setup_obs(self):
        self.participant.setup_obs("test_namespace")

    def test_handle_wi(self):
        wid = Workitem(WI_TEMPLATE)
        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "type": "submit"
        }
        wid.fields.ev.actions = [fake_action]
        wid.fields.msg = None

        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

        self.participant.obs.getPackageFileList.return_value = []
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

        wid.fields.ev.actions = []
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

if __name__ == '__main__':
    unittest.main()
