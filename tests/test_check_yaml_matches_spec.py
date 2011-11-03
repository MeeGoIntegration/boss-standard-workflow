import unittest
from ConfigParser import ConfigParser

from mock import Mock

from common_test_lib import BaseTestParticipantHandler, WI_TEMPLATE

from RuoteAMQP import Workitem

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_yaml_matches_spec"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = ConfigParser()
        self.assertRaises(RuntimeError,
                self.participant.handle_lifecycle_control, ctrl)
        ctrl.config.add_section("obs")
        ctrl.config.set("obs", "oscrc", "oscrc_file")
        self.participant.handle_lifecycle_control(ctrl)
        ctrl.config.add_section("check_yaml")
        ctrl.config.set("check_yaml", "spec_pattern", "test")
        self.participant.handle_lifecycle_control(ctrl)

    def test_setup_obs(self):
        self.participant.setup_obs("test_namespace")

    def test_handle_wi(self):
        self.mut.subprocess = Mock()
        self.mut.subprocess.Popen = Mock()
        proc = Mock()
        proc.wait.return_value = 0
        self.mut.subprocess.Popen.return_value = proc

        wid = Workitem(WI_TEMPLATE)
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

        self.participant.spec_re = Mock()
        self.participant.spec_re.search.return_value = True

        fake_action = {
            "type": "submit",
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake"
        }
        wid.fields.ev.actions = [fake_action, {"type": "test"}]
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

        wid.fields.ev.namespace = "test"

        wid.fields.msg = None

        self.participant.handle_wi(wid)

        wid.fields.ev.actions = []

if __name__ == '__main__':
    unittest.main()
