import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler, WI_TEMPLATE
from RuoteAMQP.workitem import Workitem

spec_file_content = u"""Name: boss
Version: 0.6.1
Release:1%{?dist}
Summary: MeeGo Build Orchestration Server System
Group: Productivity/Networking/Web/Utilities
License: GPL2
URL: http://wiki.meego.com/BOSS
Source0: boss_%{version}.orig.tar.gz
BuildRoot: %{name}-root-%(%{__id_u} -n)

%description
This description has some unicode: \xe1\xe1\xe1
"""

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_spec"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_setup_obs(self):
        self.participant.setup_obs("test_namespace")

    def test_valid_spec(self):
        wid = Workitem(WI_TEMPLATE)
        wid.fields.ev.actions = self.fake_actions
        self.participant.obs.getFile.return_value = spec_file_content

        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

    def test_changelog_in_spec(self):
        wid = Workitem(WI_TEMPLATE)
        wid.fields.ev.actions = self.fake_actions

        self.participant.obs.getFile.return_value = spec_file_content \
                + "\n%changelog"

        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

    def test_bad_workitem(self):
        wid = Workitem(WI_TEMPLATE)

        wid.fields.ev.actions = []
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)


if __name__ == '__main__':
    unittest.main()
