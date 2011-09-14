import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

spec_file_content = """Name: boss
Version: 0.6.1
Release:1%{?dist}
Summary: MeeGo Build Orchestration Server System
Group: Productivity/Networking/Web/Utilities
License: GPL2
URL: http://wiki.meego.com/BOSS
Source0: boss_%{version}.orig.tar.gz
BuildRoot: %{name}-root-%(%{__id_u} -n)
"""

correct_changelog = """
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1
- Add package description to README
* Fri Jul 15 2011 Ramez Hanna <rhanna@informatiq.org> - 0.6.0
- add :action => 'unregister' to boss_register participant
- New API : bump API version
* Mon Aug 30 2010 David Greaves <david@dgreaves.com> - 0.3
- Add obs-plugin
* Sun Jul 25 2010 David Greaves <david@dgreaves.com> - 0.2
- Add daemon-kit based engine
* Thu Jul 22 2010 David Greaves <david@dgreaves.com> - 0.1
- Initial minimal BOSS package
"""

incorrect_changelog = """
* Fri Jul 15 2011 Ramez Hanna <rhanna@informatiq.org> - 0.6.0
- add :action => 'unregister' to boss_register participant
- New API : bump API version
* Mon Aug 30 2010 David Greaves <david@dgreaves.com> - 0.3
- Add obs-plugin
* Sun Jul 25 2010 David Greaves <david@dgreaves.com> - 0.2
- Add daemon-kit based engine
* Thu Jul 22 2010 David Greaves <david@dgreaves.com> - 0.1
- Initial minimal BOSS package
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

    def test_quality_check(self):
        wid = Mock()
        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "relevant_changelog": "fake"
        }
        fake_action_empty = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake"
        }
        correct_fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "relevant_changelog": correct_changelog
        }
        incorrect_fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "relevant_changelog": incorrect_changelog
        }
        wid.fields.ev.actions = [fake_action]
        wid.fields.msg = None

        self.participant.obs.getFile.return_value = spec_file_content

        self.participant.quality_check(wid)

        wid.fields.ev.actions = []
        self.assertRaises(RuntimeError, self.participant.quality_check, wid)

        wid.fields.ev.actions = [fake_action_empty]
        self.assertRaises(RuntimeError, self.participant.quality_check, wid)

        wid.fields.ev.actions = [correct_fake_action]
        self.participant.quality_check(wid)
        self.assertTrue(wid.result)

        wid.fields.ev.actions = [incorrect_fake_action]
        self.participant.quality_check(wid)
        self.assertFalse(wid.result)

        self.participant.obs.getFile.return_value = "%changelog"
        self.participant.quality_check(wid)
        self.assertFalse(wid.result)

    def test_handle_wi(self):
        wid = Mock()
        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "relevant_changelog": "fake"
        }
        wid.fields.ev.actions = [fake_action]

        self.participant.handle_wi(wid)

if __name__ == '__main__':
    unittest.main()
