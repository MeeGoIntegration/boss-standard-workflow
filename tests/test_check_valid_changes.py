import unittest

from mock import Mock

from check_valid_changes import Validator, Expected, Invalid
from common_test_lib import BaseTestParticipantHandler
from RuoteAMQP.workitem import Workitem

BASE_WORKITEM = '{"fei": 1, "fields": { "params": {}, "ev": {"namespace": "test"} }}'

TEST_SPEC = u"""
%define patchlevel 1
Name: boss
Version: 0.6.%{patchlevel}
Release:1%{?dist}
Summary: MeeGo Build Orchestration Server System
Group: Productivity/Networking/Web/Utilities
License: GPL2
URL: http://wiki.meego.com/BOSS
Source0: boss_%{version}.orig.tar.gz
BuildRoot: %{name}-root-%(%{__id_u} -n)

%description
This description has some unicode: \xe1\xe1\xe1
""".encode('utf-8')


class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_valid_changes"

    good_changelog = "* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1\n- made changes"
    bad_changelog = "* Wed Aug 10 2011 invalid"
    rev_changelog = "* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1-1\n- made changes"
    badver_changelog = "* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.0\n- made changes"
    unicode_changelog = u"* Wed Aug 10 2011 Dmitry Rozhkov \xe1\xe1 <dmitry.rozhkov@nokia.com> - 0.6.1\n- made changes"
    utf8_changelog = unicode_changelog.encode('utf-8')

    def setUp(self):
        BaseTestParticipantHandler.setUp(self)
        self.wid = Workitem(BASE_WORKITEM)
        self.participant.obs.getFile.return_value = TEST_SPEC

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock()
        ctrl.message = "start"
        self.participant.handle_lifecycle_control(ctrl)

    def test_empty_actions_ok(self):
        self.wid.params.using = "relevant_changelog"
        self.wid.fields.ev.actions = []
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)

    def test_missing_actions(self):
        self.wid.params.using = "relevant_changelog"
        exc = self.assertRaises(RuntimeError,
                self.participant.handle_wi, self.wid)
        self.assertTrue("'ev.actions'" in exc.message)

    def test_missing_relevant_changelog(self):
        self.wid.params.using = "relevant_changelog"
        self.wid.fields.ev.actions = self.fake_actions
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)

    def test_missing_changelog(self):
        self.wid.params.using = "full"
        exc = self.assertRaises(RuntimeError,
                self.participant.handle_wi, self.wid)
        self.assertTrue("'changelog'" in exc.message)

    def test_unknown_mode(self):
        self.wid.params.using = "Ford Prefect"
        exc = self.assertRaises(RuntimeError,
                self.participant.handle_wi, self.wid)
        self.assertTrue("Unknown mode" in exc.message)

    def test_default_mode_full(self):
        exc = self.assertRaises(RuntimeError,
                self.participant.handle_wi, self.wid)
        self.assertTrue("'changelog'" in exc.message)

    def run_relevant_changelog(self, changelog):
        self.wid.params.using = "relevant_changelog"
        fake_action = {
            "type": "submit",
            "sourceproject": "mock",
            "sourcepackage": "fake",
            "relevant_changelog": [changelog]
        }
        self.wid.fields.ev.actions = [fake_action]
        self.participant.handle_wi(self.wid)

    def test_relevant_bad(self):
        self.run_relevant_changelog(self.bad_changelog)
        self.assertFalse(self.wid.result)

    def test_relevant_good(self):
        self.run_relevant_changelog(self.good_changelog)
        self.assertTrue(self.wid.result)

    def test_relevant_rev(self):
        self.run_relevant_changelog(self.rev_changelog)
        self.assertTrue(self.wid.result)

    def test_relevant_unicode(self):
        self.run_relevant_changelog(self.unicode_changelog)
        self.assertTrue(self.wid.result)

    def test_relevant_utf8(self):
        self.run_relevant_changelog(self.utf8_changelog)
        self.assertTrue(self.wid.result)

    def test_relevant_badversion(self):
        self.run_relevant_changelog(self.badver_changelog)
        self.assertFalse(self.wid.result)

    def test_full_bad(self):
        self.wid.params.using = "full"
        self.wid.fields.changelog = self.bad_changelog
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)

    def test_full_good(self):
        self.wid.params.using = "full"
        self.wid.fields.changelog = self.good_changelog
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)

    def test_full_rev(self):
        self.wid.params.using = "full"
        self.wid.fields.changelog = self.rev_changelog
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)

    def test_full_unicode(self):
        self.wid.params.using = "full"
        self.wid.fields.changelog = self.unicode_changelog
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)

    def test_full_utf8(self):
        self.wid.params.using = "full"
        self.wid.fields.changelog = self.utf8_changelog
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)

    def test_full_badversion(self):
        self.wid.params.using = "full"
        self.wid.fields.changelog = self.badver_changelog
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)

class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = Validator()

    def assert_unexpected(self, found, lineno, changelog):
        try:
            self.validator.validate(changelog)
            self.fail("Validator accepted invalid changelog")
        except Expected, exobj:
            if exobj.found != found or exobj.lineno != lineno:
                raise
            self.assertTrue("unexpected" in str(exobj))

    def assert_invalid(self, invalid, missing, lineno, changelog):
        try:
            self.validator.validate(changelog)
            self.fail("Validator accepted invalid changelog")
        except Invalid, exobj:
            if exobj.invalid != invalid or exobj.missing != missing \
               or exobj.lineno != lineno:
                raise
            self.assertTrue("Invalid" in str(exobj))

    def test_good_changelog(self):
        self.validator.validate("""\
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1
- made changes
  some of them were difficult
- made some more changes

* Wed Aug 10 2011 Multiple Part Name <dmitry.rozhkov@nokia.com> - 0.6.0
- transcendent version

* Wed Aug 10 2011 Singlewordname <dmitry.rozhkov@nokia.com> - 0.5.8
- exotic version

* Wed Aug 10 2011 Version with revision <dmitry.rozhkov@nokia.com> - 0.5-1
- initial version
""")

    def test_extra_space_accepted(self):
        self.validator.validate(
"* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1 \n"
"- made changes\n"
"  some of them were difficult  \n"
"- made some more changes\n")

    def test_unexpected_header(self):
        self.assert_unexpected("header", 2, """\
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.0
- initial version
""")

    def test_unexpected_continuation(self):
        self.assert_unexpected("continuation line", 2, """\
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1
  made changes
- made some more changes

* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.0
- initial version
""")

    def test_missing_blank(self):
        self.assert_unexpected("header", 3, """\
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1
- made changes
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.0
- initial version
""")
        self.assert_unexpected("header", 4, """\
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1
- made changes
  some of them were difficult
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.0
- initial version
""")

    def test_missing_body(self):
        self.assert_unexpected("blank", 2, """\
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1

* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.0
- initial version
""")

    def test_unexpected_blank(self):
        self.assert_unexpected("blank", 2, """\
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1

- initial version
""")

    def test_split_body(self):
        self.assert_unexpected("body", 4, """\
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1
- made changes

- made some more changes

* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.0
- initial version
""")

    def test_missing_group(self):
        self.assert_invalid("header", None, 1,
            '* Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1')
        self.assert_invalid("header", "author", 1,
            '* Wed Aug 10 2011 <dmitry.rozhkov@nokia.com> - 0.6.1')
        self.assert_invalid("header", "space", 1,
            '* Wed Aug 10 2011 Dmitry Rozhkov<dmitry.rozhkov@nokia.com> - 0.6')
        self.assert_invalid("header", "email", 1,
            '* Wed Aug 10 2011 Dmitry Rozhkov - 0.6.1')
        self.assert_invalid("header", "hyphen", 1,
            '* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> 0.6.1')
        self.assert_invalid("header", "hyphen", 1,
            '* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com>')
        self.assert_invalid("header", "version", 1,
            '* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> -')

    def test_bad_date(self):
        self.assert_invalid("date", None, 1,
            '* Wed Frd 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6')
        self.assert_invalid("date", None, 1,
            '* We Jul 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6')
        self.assert_invalid("date", None, 1,
            '* Jul 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6')
        self.assert_invalid("date", None, 1,
            '* Wed 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6')
        self.assert_invalid("date", None, 1,
            '* Wed Jul 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6')
        self.assert_invalid("date", None, 1,
            '* Wed Jul 10 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6')
        self.assert_invalid("date", None, 1,
            '* Wed Jul 10 201 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6')

    def test_bad_email_ok(self):
        """Email address validation has been relaxed in order to allow
           a variety of anti-spam email obfuscation techniques to work."""
        self.validator.validate(
         '* Wed Aug 10 2011 Dmitry Rozhkov <dmitry[AT]nokia.com> - 1.2')
        self.validator.validate(
         '* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov at nokia> - 1.2')

    def test_bad_header(self):
        self.assert_invalid("header", None, 1,
            '* Wed Aug 10 2011 Dmitry Rozhkov <dmitry@nokia.com> - 0.6.1 d')

    def test_leading_spaces(self):
        self.assert_unexpected("continuation line", 1,
            ' * Wed Aug 10 2011 Dmitry Rozhkov <dmitry@nokia.com> - 0.6.1')
        self.assert_unexpected("continuation line", 2, """\
* Wed Aug 10 2011 Dmitry Rozhkov <dmitry@nokia.com> - 0.6.1
 - initial version
""")

    def test_unrecoqnized_line(self):
        self.assert_unexpected("garbage", 1,
"""This here is unrecoqnized line
- initial version
""")


if __name__ == '__main__':
    unittest.main()
