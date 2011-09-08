import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_has_valid_repo"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_setup_obs(self):
        self.participant.setup_obs("test_namespace")

    def test_get_target_repo(self):
        self.participant.obs.getProjectRepositories.return_value = []
        self.assertFalse(self.participant.get_target_repo(None, None, None, None))

        self.participant.obs.getProjectRepositories.return_value = ['fake']
        self.participant.obs.getRepositoryTargets.return_value = ['fake']
        self.participant.get_target_repo(None, None, None, None)

    def test_quality_check(self):
        wid = Mock()
        fake_action = {
            "sourceproject": "fake"
        }
        wid.fields.ev.actions = [fake_action]
        wid.fields.msg = None
        wid.fields.archs = ['fake_arch']

        self.participant.quality_check(wid)

        wid.fields.project = None
        self.assertRaises(RuntimeError, self.participant.quality_check, wid)

    def test_handle_wi(self):
        wid = Mock()
        fake_action = {
            "sourceproject": "fake"
        }
        wid.fields.ev.actions = [fake_action]
        wid.fields.archs = ['fake_arch']

        self.participant.handle_wi(wid)

if __name__ == '__main__':
    unittest.main()
