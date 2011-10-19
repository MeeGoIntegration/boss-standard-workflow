import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_package_built_at_source"

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
        wid = self.fake_workitem
        fake_action = {
            "type" : "submit",
            "sourceproject": "fake",
            "sourcepackage": "fake"
        }
        wid.fields.ev.actions = [fake_action]
        wid.fields.msg = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        wid.fields.archs = ['fake_arch']
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        wid.fields.targetrepo = 'fake_repo'

        self.participant.obs.isPackageSucceeded.return_value = False
        self.participant.handle_wi(wid)


if __name__ == '__main__':
    unittest.main()
