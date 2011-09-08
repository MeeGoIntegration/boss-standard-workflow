import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "get_relevant_changelog"

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

        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "targetpackage": "fake",
            "targetproject": "fake"
        }
        wid.fields.ev.actions = [fake_action]
        wid.params.compare = "last_revision"
        self.participant.handle_wi(wid)

if __name__ == '__main__':
    unittest.main()
