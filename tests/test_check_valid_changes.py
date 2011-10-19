import unittest

from mock import Mock

from check_valid_changes import Validator, Expected, Invalid
from common_test_lib import BaseTestParticipantHandler
from RuoteAMQP.workitem import Workitem

BASE_WORKITEM = '{"fei": 1, "fields": { "params": {}, "ev": {"namespace": "test"} }}'

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_valid_changes"

    good_changelog = "* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia.com> - 0.6.1\n- made changes"
    bad_changelog = "* Wed Aug 10 2011 invalid"

    def setUp(self):
        BaseTestParticipantHandler.setUp(self)
        self.wid = Workitem(BASE_WORKITEM)
        self.participant.obs.getFile.return_value = "Version: 0.6.1"

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
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)
        self.assertTrue("actions missing" in self.wid.fields.msg[-1])

    def test_missing_relevant_changelog(self):
        self.wid.params.using = "relevant_changelog"
        fake_action = {
            "type": "submit",
            "sourcepackage": "mock"
        }
        self.wid.fields.ev.actions = [fake_action]
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)
        self.assertTrue("Missing relevant_changelog" in self.wid.fields.msg[-1])

    def test_missing_changelog(self):
        self.wid.params.using = "full"
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)
        self.assertTrue("changelog missing" in self.wid.fields.msg[-1])

    def test_unknown_mode(self):
        self.wid.params.using = "Ford Prefect"
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)
        self.assertTrue("Unknown mode" in self.wid.fields.msg[-1])

    def test_default_mode_full(self):
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)
        self.assertTrue("changelog missing" in self.wid.fields.msg[-1])

    def test_relevant_bad(self):
        self.wid.params.using = "relevant_changelog"
        fake_action = {
            "type": "submit",
            "sourcepackage": "fake",
            "relevant_changelog": [self.bad_changelog]
        }
        self.wid.fields.ev.actions = [fake_action]
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)

    def test_relevant_good(self):
        self.wid.params.using = "relevant_changelog"
        fake_action = {
            "type": "submit",
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "relevant_changelog": [self.good_changelog]
        }
        self.wid.fields.ev.actions = [fake_action]
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)

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

    def test_bad_version(self):
        self.wid.params.using = "full"
        self.wid.fields.changelog = self.good_changelog
        self.participant.obs.getFile.return_value = "Version: 0.6.0"
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

    def test_bad_email(self):
        self.assert_invalid("email", None, 1,
            '* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov.nokia.com> - 1.2')
        self.assert_invalid("email", None, 1,
            '* Wed Aug 10 2011 Dmitry Rozhkov <dmitry.rozhkov@nokia> - 1.2')

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
