#!/usr/bin/python
"""Email notification participant
This participant tries to be the one stop solution for process email
notification needs. It supports TO, CC, attachments etc ..

.. warning::
   Attachments are expected to be local files.
   For example attaching an OBS build log would mean installing the getbuildlog
   participant on the same machine and running it first in the process.

A suggested approach::

  set 'f:ml1' => ["mail1@example.com", "mail2@example.com", "mail3@example.com"]
  set 'f:ml2' => ["mail3@example.com", "mail4@example.com", "mail5@example.com"]
  notify :template => 'ml1', :subject => 'Mail for ml1', :mail_to => '$ml1'
  notify :template => 'ml2', :subject => 'Mail for ml2', :mail_to => '$ml1'

Note that there are no curly brackets around the $ml1 variables to
permit the literal list to be passed to the parameter.

The text of the emails is based on
`Cheetah templates <http://www.cheetahtemplate.org/>`_ that you provide.
The workitem fields are available to the templates under $f and request data is
available under $req. References to undefined fields are replaced with empty
strings.


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
      option, and in cheetah format. All workitem fields except mail_to and
      mail_cc are passed to the temlpate.
   mail_to(list):
      A list of emails to send to.
   mail_cc(list)
      A list of emails to CC to.
   mail_from(string)
      Email to use as sender address
   msg(list)
      List of strings that contain some information to be emailed
   attachments(list)
      List of filenames that locally readable, which are to be attached to the
      email. They must be under one of the directories listed in the
      "allowed_attachment_dirs" config option.

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
   dont_send(bool)
      Debug parameter: If set the email is printed to the log but not actually
      sent

:term:`Workitem` fields OUT :

:Returns:
   result(Boolean):
      True if everything went OK, False otherwise
   mail_to(list):
      Cleared, left empty
   mail_cc(list):
      Cleared, left empty
"""

import os
import time
import smtplib
import mimetypes
from collections import defaultdict
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr
from Cheetah.Template import Template
from Cheetah.NameMapper import NotFound

COMMASPACE = ', '

class ForgivingDict(defaultdict):
    """A dictionary that resolves unknown keys to empty strings,
    for use with Cheetah templates.
    """

    def __init__(self, value=()):
        # ForgivingDict is its own default value. It can act as either
        # an empty string or as a forgiving empty container or as an
        # empty iterator, depending on what the caller tries to do with it.
        defaultdict.__init__(self, ForgivingDict, value)

    def __str__(self):
        if not self:
            return ""
        return defaultdict.__str__(self)

    def has_key(self, _key):
        """Cheetah.NameMapper sometimes tries has_key before looking up a key,
           so pretend all keys are valid."""
        # Debugging this is difficult because Cheetah's compiled namemapper
        # module behaves differently from the python Cheetah.NameMapper.
        return True


def fixup_utf8(value):
    """Encountering non-ascii data in a str makes Cheetah sad.
    Work around it by requiring all non-ascii data to be utf8,
    and converting it to unicode objects."""
    if isinstance(value, str):
        return value.decode('utf8', 'replace')
    return value


def general_map(value, dicts=dict, lists=list, values=None):
    """Transform a nested container structure, replacing mappings and
       sequences with new ones constructed with the 'dicts' and 'lists'
       constructors, and transforming values with the 'values' function.
       If values is None or not supplied, then leave the values unchanged.
       Strings are treated as values."""
    def transform(value):
        if isinstance(value, basestring):
            if values is None:
                return value
            return values(value)
        if hasattr(value, 'iteritems'):
            return dicts((k, transform(v)) for (k, v) in value.iteritems())
        if hasattr(value, '__iter__'):
            return lists(transform(v) for v in value)
        if values is None:
            return value
        return values(value)
    return transform(value)


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
    """Keep only unique addresses that are not already in relative_to.
       Addresses are compared on just the email part, but the result list
       provides the full address.
       For example 'Richard Braakman <rbraakma@example.com>' and
       'Richard <rbraakma@example.com>' are considered the same address.
    """
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

    try:
        mbody = MIMEText(body.encode('ascii'), 'plain')
    except UnicodeEncodeError:
        mbody = MIMEBase('text', 'plain')
        mbody['Content-Transfer-Encoding'] = '8bit'
        mbody.set_payload(body.encode('utf-8'), 'utf-8')
    # attachments need multipart message
    if attachments:
        msg = MIMEMultipart()
        msg.add_header('Content-Disposition', 'body')
        msg.attach(mbody)
    else:
        msg = mbody

    if attachments:
        for name in attachments:
            try:
                msg = add_attachment(msg, name)
            except Exception, exobj:
                self.log.info(exobj)
                self.log.info("Failed to attach %s" % name)

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
        smtp = None  # placeholder so except handler can call smtp.quit()
        try:
            smtp = smtplib.SMTP(self.smtp_server)
            result = smtp.sendmail(sender, tos, msg.as_string())
            smtp.quit()
            refused = []
            for i in result.keys():
                refused.append("%s : %s" % (i, result[i]))
            self.log.info("Mail sent.")
            if refused:
                self.log.info("Delivery refused for: %s" % COMMASPACE.join(refused))
        except smtplib.SMTPException, exobj:
            self.log.info("Error: unable to send email: %s" % exobj)
            if smtp:
                smtp.quit()
            if not retry > 2:
                retry += 1
                time.sleep(10)
                self.log.info("Retrying %s" % retry)
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
        wid.fields.mail_to = []
        wid.fields.mail_cc = []

        if wid.params.extra_msg:
            wid.fields.msg.append(wid.params.extra_msg)

        if not subject:
            raise RuntimeError("Missing mandatory field or param 'subject'")

        if not (template_body or template_name):
            raise RuntimeError("Both of field or param 'template_body' and "
                    "'template_name' missing")

        if template_body and template_name:
            raise RuntimeError("Both field or param 'template_body' and "
                    "'template_name' defined")

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

        if not mail_to and not mail_cc:
            err = "No recipients listed; not sending mail."
            self.log.info(err)
            wid.fields.msg.append(err)
            wid.result = True
            return

        searchlist = {'f': general_map(wid.fields.as_dict(),
                                       dicts=ForgivingDict, values=fixup_utf8)}
        searchlist['req'] = searchlist['f']['req'] or ForgivingDict()

        # Try the template but if there's an error, re-do with the
        # more informative errorCatcher and send to the log
        try:
            template = Template(template_body, searchList=searchlist)
            message = unicode(template)
        except NotFound, err:
            # You can't set the errorCatcher using a class - this is
            # pattern a) usage
            self.log.info("Error processing template - trying with errorCatcher")
            template = Template("#errorCatcher BigEcho\n" + template_body,
                                searchList=searchlist)
            message = unicode(template)
            self.log.info("Processed template with highlights:")
            self.log.info(message)
            raise
        

        memail = prepare_email(mail_from, mail_to, mail_cc,
                               subject, message, attachments)

        # Don't actually send the email
        if wid.params.dont_send:
            self.log.info(memail)
        else:
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
            self.smtp_server = ctrl.config.get("notify","smtp_server")
            self.email_store = ctrl.config.get("notify","email_store")
            self.default_sender = ctrl.config.get("notify","default_sender")
            okdirs = ctrl.config.get("notify", "allowed_attachment_dirs")
            self.allowed_attachment_dirs = okdirs.split()

    def handle_wi(self, wid):
        """Handle a workitem: send mail."""

        self.handle_notification(wid)
