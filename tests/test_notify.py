import unittest

from mock import Mock

import notify

class TestParticipantHandler(unittest.TestCase):

    def setUp(self):
        self.participant = notify.ParticipantHandler()
        self.wid = Mock()
        self.wid.params.template = "template.tpl"
        self.wid.fields.template_str = "fake template"
        self.wid.fields.msg = []
        self.wid.fields.From = "Fake User <fakeuser@example.com>"
        self.wid.fields.To = "fakeuser@example.com"
        self.wid.fields.email = "fakeuser@example.com"
        self.wid.fields.Cc = "fakeuser@example.com"
        self.wid.fields.attachments = ["tests/test_data/template.tpl", "fake"]
        self.wid.params.extra_msg = "fake extra message"
        self.participant.email_store = "tests/test_data"
        smtp = Mock()
        smtp.sendmail.return_value = {"fake_key": "fake_value"}
        notify.smtplib = Mock()
        notify.smtplib.SMTP.return_value = smtp

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_handle_wi(self):
        self.participant.handle_wi(self.wid)

    def test_handle_notification(self):
        self.participant.handle_notification(self.wid)

        # Test setting defaults
        self.wid.fields.From = ""
        self.wid.fields.To = ""
        self.wid.fields.emails = ""
        self.participant.handle_notification(self.wid)

        self.wid.params.template = ""
        self.wid.fields.template_str = ""
        self.assertRaises(RuntimeError, self.participant.handle_notification, self.wid)

if __name__ == '__main__':
    unittest.main()
