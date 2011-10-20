import unittest

from mock import Mock
from RuoteAMQP import Workitem

from common_test_lib import BaseTestParticipantHandler, WI_TEMPLATE

spec_file_content = """Name: test
Version: 0.1
Release:1
Summary: Test
Group: Development/Debuggers
License: GPL2
Source0: test.tar.gz
%description
Test package
"""

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

    def test_get_spec_sources(self):
        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "type": "submit"
        }
        self.assertEqual(self.participant.get_spec_sources(fake_action, []),
                None)
        self.participant.obs.getFile.return_value = "bad spec"
        self.assertEqual(self.participant.get_spec_sources(fake_action,
            ["test.spec"]), None)

        self.participant.obs.getFile.return_value = spec_file_content
        sources = self.participant.get_spec_sources(fake_action, ["test.spec"])
        self.assertEqual(self.participant.obs.getFile.call_args[0],
                ("fake", "fake", "test.spec", "fake"))
        self.assertEqual(sources, ["test.tar.gz"])


if __name__ == '__main__':
    unittest.main()
