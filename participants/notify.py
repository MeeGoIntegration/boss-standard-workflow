#!/usr/bin/python
"""Email notification participant
This participant tries to be the one stop solution for process email
notification needs. It supports TO, CC, attachments etc ..

.. warning::
   Attachments are expected to be local files.
   For example attaching an OBS build log would mean installing the getbuildlog
   participant on the same machine and running it first in the process.

:term:`Workitem` fields IN :

:Parameters:
   subject(string):
       The subject of the email
   template_body(string):
      The cheetah template string to use in generating the email.
      Not used if fields.template or params.template is present.
   template(string):
      The name of a template file to use in generating the email. The file
      is expected to be in the path specified by the "email_store" config
      option, and in cheetah format.
   mail_to(list):
      A list of emails to send to
   mail_cc(list)
      A list of emails to CC to
   mail_from(string)
      Email to use as sender address
   msg(list)
      List of strings that contain some information to be emailed
   attachments(list)
      List of filenames that locally readable, which are to be attached to the
      email.

:term:`Workitem` params IN

:Parameters:
   subject(string):
      Overrides subject field.
   template_body(string):
      Overrides template_body field.
   template(string):
      Overrides template field. Only one of template or template_body
      may be present.
   mail_to(list):
      A list of emails to send to.
      Will be merged with fields.mail_to if both are present.
   mail_cc(list):
      A list of emails to CC to.
      Will be merged with fields.mail_cc if both are present.
   mail_from(string):
      Overrides mail_from field.
   extra_msg(string):
      Extra message appended to the list obtained from the msg field

:term:`Workitem` fields OUT :

:Returns:
   result(Boolean):
      True if everything went OK, False otherwise

"""

import os
import time
import smtplib
import mimetypes
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr
from Cheetah.Template import Template

COMMASPACE = ', '

def allowed_file(path, dirs):
    """Return true iff the given path is in one of the dirs.
        :param path: user-supplied path
        :type path: string
        :param dirs: list of allowed dirs, should be absolute
    """
    for okdir in dirs:
        if path.startswith(okdir + os.sep):
            return True
    return False

def remove_duplicate_addrs(addrs, relative_to=None):
    seen = set(parseaddr(addr)[1] for addr in (relative_to or []))
    result = []
    for addr in addrs:
        _name, email = parseaddr(addr)
        if email not in seen:
            seen.add(email)
            result.append(addr)
    return result

def normalize_addr_header(hdr):
    """ Helper routine to normalize the charset of headers
        :param hdr: Header to be normalized
        :type hdr: string
    """

    # Header class is smart enough to try US-ASCII, then the charset we
    # provide, then fall back to UTF-8.
    header_charset = 'ISO-8859-1'

    # Split real name (which is optional) and email address parts
    name, addr = parseaddr(hdr)

    if name:
        # We must always pass Unicode strings to Header, otherwise it
        # will use RFC 2047 encoding even on plain ASCII strings.
        name = str(Header(unicode(name), header_charset))

    # Make sure email addresses do not contain non-ASCII characters
    addr = addr.encode('ascii')

    return formataddr((name, addr))

def add_attachment(message, path):
    """ Add an attachment to an email
        :param message: The generated message object
        :type message: MIMEMultipart object
        :param path: Full path to the file being attached
        :type path: string
    """
    # adapted from
    # http://docs.python.org/release/2.6.2/library/email-examples.html#id1
    # Guess the content type based on the file's extension.  Encoding
    # will be ignored, although we should check for simple things like
    # gzip'd or compressed files.
    ctype, encoding = mimetypes.guess_type(path)
    if ctype is None or encoding is not None:
        # No guess could be made, or the file is encoded (compressed),
        # so use a generic bag-of-bits type.
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    if maintype == 'text':
        fp = open(path)
        # Note: we should handle calculating the charset
        msg = MIMEText(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == 'image':
        fp = open(path, 'rb')
        msg = MIMEImage(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == 'audio':
        fp = open(path, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=subtype)
        fp.close()
    else:
        fp = open(path, 'rb')
        msg = MIMEBase(maintype, subtype)
        msg.set_payload(fp.read())
        fp.close()
        # Encode the payload using Base64
        encoders.encode_base64(msg)
    # Set the filename parameter
    msg.add_header('Content-Disposition', 'attachment',
                   filename=os.path.basename(path))
    message.attach(msg)

    return message

def prepare_email(sender, tos, ccs, subject, body, attachments=None):
    """Prepare an email.
    All arguments should be Unicode strings (plain ASCII works as well).

    Only the real name part of sender and recipient addresses may contain
    non-ASCII characters.

    The email will be properly MIME encoded.
    The charset of the email will be the first one out of US-ASCII,
    ISO-8859-1 and UTF-8 that can represent all the characters occurring in
    the email.

    attachments is a list of filenames to be attached
    """

    # attachments need multipart message
    msg = MIMEMultipart()
    msg.add_header('Content-Disposition', 'body')
    mbody = MIMEText(body.encode('ascii','replace'), 'plain')
    msg.attach(mbody)
    if attachments:
        for name in attachments:
            try:
                msg = add_attachment(msg, name)
            except Exception, exobj:
                print exobj
                print "Failed to attach %s" % name

    # Normalize all headers
    msg['Subject'] = Header(unicode(subject), 'ISO-8859-1')
    msg['From'] = normalize_addr_header(sender)
    msg['To'] = COMMASPACE.join(map(normalize_addr_header, tos))
    if ccs:
        msg['Cc'] = COMMASPACE.join(map(normalize_addr_header, ccs))
    return msg

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.smtp_server = None
        self.email_store = None
        self.default_sender = None
        self.allowed_attachment_dirs = None

    def send_email(self, sender, tos, msg, retry=1):
        """ Sends the generated email using an smtp server

            :param sender: From email address
            :type sender: string
            :param tos: email addresses to send to
            :type tos: list
            :param msg: The generated message object
            :type msg: MIMEMultipart object
        """
        # Send the message via SMTP
        try:
            smtp = smtplib.SMTP(self.smtp_server)
            result = smtp.sendmail(sender, tos, msg.as_string())
            smtp.quit()
            refused = []
            for i in result.keys():
                refused.append("%s : %s" % (i, result[i]))
            print "Mail sent. Refused: %s" \
                                     % (COMMASPACE.join(refused))
        except smtplib.SMTPException, exobj:
            print "Error: unable to send email: %s" % exobj
            if not retry > 2:
                retry += 1
                time.sleep(10)
                print "Retrying %s" % ( str(retry) )
                smtp.quit()
                self.send_email(sender, tos, msg, retry)

    def handle_notification(self, wid):
        """ Extracts the needed data from the workitem, prepares the email and
            then sends it
            :param wid: Workitem
            :type wid: object
        """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []

        subject = wid.params.subject or wid.fields.subject
        template_body = wid.params.template_body or wid.fields.template_body
        template_name = wid.params.template or wid.fields.template
        mail_from = wid.params.mail_from or wid.fields.mail_from \
                    or self.default_sender
        mail_to = (wid.fields.mail_to or []) + (wid.params.mail_to or [])
        mail_cc = (wid.fields.mail_cc or []) + (wid.params.mail_cc or [])

        if wid.params.extra_msg:
            wid.fields.msg.append(wid.params.extra_msg)

        if not subject:
            wid.error = "Mandatory field/param 'subject' missing"
            wid.fields.msg.append(wid.error)
            raise RuntimeError(wid.error)

        if not mail_to:
            wid.error = "Mandatory field/param 'mail_to' missing"
            wid.fields.msg.append(wid.error)
            raise RuntimeError(wid.error)

        if not (template_body or template_name):
            wid.error = "template_body and template_name both missing"
            wid.fields.msg.append(wid.error)
            raise RuntimeError(wid.error)

        if template_body and template_name:
            wid.error = "template_body and template_name both defined"
            wid.fields.msg.append(wid.error)
            raise RuntimeError(wid.error)

        if template_name:
            template_fname = os.path.join(self.email_store, template_name)
            with open(template_fname) as fil:
                template_body = fil.read()

        attachments = []
        for attachment in (wid.fields.attachments or []):
            attachment = os.path.abspath(attachment)
            if not allowed_file(attachment, self.allowed_attachment_dirs):
                wid.fields.msg.append("Refusing to attach %s" % attachment)
            elif not os.path.isfile(attachment):
                wid.fields.msg.append("Could not find attachment %s"
                                      % attachment)
            else:
                attachments.append(attachment)

        mail_to = remove_duplicate_addrs(mail_to)
        mail_cc = remove_duplicate_addrs(mail_cc, relative_to=mail_to)
            
        template = Template(template_body, searchList=[wid.fields.as_dict()])
        template.msg = "\n".join(wid.fields.msg)
        message = str(template)

        memail = prepare_email(mail_from, mail_to, mail_cc,
                               subject, message, attachments)

        self.send_email(mail_from, mail_to + mail_cc, memail)

        wid.result = True

    def handle_wi_control(self, ctrl):
        """Job control thread"""
        pass

    def handle_lifecycle_control(self, ctrl):
        """ :param ctrl: Control object passed by the EXO.
                         If the message attribute is "start", some
                         configuration variables are extracted from the config
                         attribute:
                         * smtp_server : hostname or IP address of smtp server
                         * email_store : path where email templates reside
                         * default_sender : default from address
            :type ctrl: object
        """

        if ctrl.message == "start":
            self.smtp_server = ctrl.config.get("DEFAULT","smtp_server")
            self.email_store = ctrl.config.get("DEFAULT","email_store")
            self.default_sender = ctrl.config.get("DEFAULT","default_sender")
            okdirs = ctrl.config.get("DEFAULT", "allowed_attachment_dirs")
            self.allowed_attachment_dirs = okdirs.split()

    def handle_wi(self, wid):
        """Handle a workitem: send mail."""
        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.handle_notification(wid)
