import os
from mock import Mock
import smtplib
import time
import unittest

from RuoteAMQP.workitem import Workitem

import notify


BASE_WORKITEM = '{"fei": 1, "fields": { "params": {}, "ev": {} }}'
TEMPLATE_BODY = """
Hello, this is a mail from the unit tests of the notify participant,
specifically the template_body variant.
You may be interested in these messages:
#for $item in $msg
 * $item
#end for

Thank you and have a nice day.
"""


class TestParticipantHandler(unittest.TestCase):

    def setUp(self):
        self.participant = notify.ParticipantHandler()
        self.wid = Workitem(BASE_WORKITEM)
        self.wid.fields.msg = ["message 1", "message 2"]
        self.wid.params.subject = "Fake Mail Subject"
        self.wid.params.template = "mail_template.tpl"
        self.wid.params.mail_from = "Fake Sender <fakesender@example.com>"
        self.wid.params.mail_to = ["Fake User <fakeuser@example.com>"]
        self.participant.email_store = "tests/test_data"

        smtp = Mock(spec_set=smtplib.SMTP)
        smtp.sendmail.side_effect = self.mock_sendmail
        notify.smtplib = Mock()
        notify.smtplib.SMTP.return_value = smtp
        notify.smtplib.SMTPException = smtplib.SMTPException

        self.expect_sender = self.wid.params.mail_from[:]
        self.expect_recipients = self.wid.params.mail_to[:]
        self.in_msg = self.wid.fields.msg
        self.in_msg.append("Subject: %s" % self.wid.params.subject)
        self.sendmail_count = 0
        self.sendmail_fail = 0
        self.rejections = {}

    def mock_sendmail(self, from_addr, to_addrs, msg,
                      mail_options=[], rcpt_options=[]):
        """Check that sendmail was called with the right arguments.
           The addresses are normalized by this time so the expect_
           variables must also contain normalized addresses.
           Since setUp uses addresses that are already in normal form
           this is not really a problem.
        """
        self.sendmail_count += 1
        self.assertEqual(from_addr, self.expect_sender)
        self.assertEqual(sorted(to_addrs), sorted(self.expect_recipients))
        for text in self.in_msg:
            self.assertTrue(text in msg, "Mail did not contain: %s" % text)
        if self.sendmail_fail > 0:
            self.sendmail_fail -= 1
            raise smtplib.SMTPException("mock failure")
        return self.rejections

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_normal_case(self):
        self.in_msg.append("To: %s" % self.wid.params.mail_to[0])
        self.in_msg.append("From: %s" % self.wid.params.mail_from)
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)
        self.assertEqual(self.wid.fields.mail_to, [])
        self.assertEqual(self.wid.fields.mail_cc, [])

    def test_subject_override(self):
        """Test that params.subject overrides fields.subject"""
        self.wid.fields.subject = "Unused Mail Subject"
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_template_override(self):
        """Test that params.template overrides fields.template"""
        self.wid.fields.template = "wrong_template.tpl"
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_template_body_override(self):
        """Test that params.template_body overrides fields.template_body"""
        self.wid.params.template = None
        self.wid.params.template_body = TEMPLATE_BODY
        self.wid.fields.template_body = "wrong_template"
        self.in_msg.append("template_body variant")
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_template_args_exclusion(self):
        self.wid.fields.template_body = TEMPLATE_BODY
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)

    def test_mail_from_override(self):
        """Test that params.mail_from overrides fields.mail_from"""
        self.wid.fields.template = "Unused Sender <unusedsender@example.com>"
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_mail_to_merge(self):
        """Test that params.mail_to is added to fields.mail_to"""
        self.wid.fields.mail_to = ["Extra Recipient <extrauser@example.com>"]
        self.expect_recipients += self.wid.fields.mail_to
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_mail_cc(self):
        """Test that addresses in the cc list are added to the Cc header"""
        self.wid.fields.mail_cc = ["Extra Recipient <extrauser1@example.com>"]
        self.expect_recipients += self.wid.fields.mail_cc
        self.in_msg.append("Cc: %s" % self.wid.fields.mail_cc[0])
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_mail_cc_merge(self):
        """Test that params.mail_cc is added to fields.mail_cc"""
        self.wid.fields.mail_cc = ["Extra Recipient <extrauser1@example.com>"]
        self.expect_recipients += self.wid.fields.mail_cc
        self.wid.params.mail_cc = ["Extra Recipient <extrauser2@example.com>"]
        self.expect_recipients += self.wid.params.mail_cc
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_mail_cc_merge_duplicates(self):
        """Test that duplicate addresses are weeded out when merging mail_cc."""
        self.wid.fields.mail_cc = ["Extra Recipient <extrauser1@example.com>"]
        self.wid.params.mail_cc = ["Extra Recipient <extrauser1@example.com>"]
        self.expect_recipients += self.wid.fields.mail_cc
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_mail_cc_merge_duplicate_to(self):
        """Test that duplicates between To and Cc are weeded out."""
        self.wid.params.mail_cc = self.wid.params.mail_to
        # Even when the name is different but the address the same
        self.wid.params.mail_cc += ["Same Fake User <fakeuser@example.com>"]
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_extra_msg(self):
        self.wid.params.extra_msg = "Extra Message"
        self.in_msg.append("Extra Message")
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_attachments(self):
        self.participant.allowed_attachment_dirs = \
           ["/tmp", os.path.abspath("tests")]
        self.wid.fields.attachments = ["tests/test_data/attachment.txt"]
        self.in_msg.append("This is an attachment")
        self.in_msg.append("filename=attachment.txt")
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_varied_attachments(self):
        self.participant.allowed_attachment_dirs = \
           ["/tmp", os.path.abspath("tests")]
        self.wid.fields.attachments = []
        for ext in 'txt.gz', 'png', 'wav':
            name = "tests/test_data/attachment." + ext
            self.wid.fields.attachments.append(name)
            self.in_msg.append("filename=%s" % name)
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_missing_attachment(self):
        self.participant.allowed_attachment_dirs = \
           ["/tmp", os.path.abspath("tests")]
        self.wid.fields.attachments = ["tests/test_data/missing.txt"]
        self.in_msg.append("Could not find attachment")
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_refused_attachments(self):
        self.participant.allowed_attachment_dirs = []
        attachment = "tests/test_data/attachment.txt"
        self.wid.fields.attachments = [attachment]
        self.in_msg.append("Refused to attach %s" % os.path.abspath(attachment))
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_zero_recipients(self):
        self.wid.params.mail_to = []
        self.wid.check_recipients = []
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 0)
        self.assertTrue(self.wid.result)
        for msg in self.wid.fields.msg:
            if "not sending" in msg:
                break
        else:
            self.fail("Did not find msg about empty recipient list")

    def test_recipient_reject(self):
        self.rejections['fakeuser@example.com'] = 'no reason'
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 1)
        self.assertTrue(self.wid.result)

    def test_smtp_retry(self):
        notify.time = Mock()  # disable sleep
        self.sendmail_fail = 1
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.sendmail_count, 2)
        self.assertTrue(self.wid.result)
        notify_time = time

if __name__ == '__main__':
    unittest.main()
