import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "get_changelog"

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
        wid = Mock()

        wid.fields.project = "fake_project"
        wid.fields.package = "fake_package"
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

        wid.fields.project = ""
        wid.fields.package = ""
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

if __name__ == '__main__':
    unittest.main()
