#!/usr/bin/python
"""
Bugzilla participant

Interacts with bugzilla to:
* add comments to bugs
* change bug status
* verify bug mentioned

The comment can be populated using a string or a template.

.. warning::
   The get_relevant_changelog participant should have be run first to fetch
   the relevant changelog entries

:term:`Workitem` fields IN

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`.
   package(string):
      name of the package being handled, if actions is not provided.
   relevant_changelog(list):
      a field containing changelog entries in a list, if actions is not provided
   platform(string):
     The name of the platform to which the packages belong. This is used to
     select which bug trackers to talk to according to the configuration file.

:term:`Workitem` params IN

:Parameters:
   status(string):
      UNCONFIRMED/NEW/ASSIGNED/REOPENED/RESOLVED/VERIFIED/CLOSED
      Set bugs to this status
   check_status(string):
      Takes same values as status
      Verifies that bugs have this status
   resolution(string):
      FIXED/INVALID/WONTFIX/DUPLICATE/WORKSFORME/MOVED
      Set bugs to this resolution when setting status
   check_resolution(string):
      Takes same values as resolution
      Verifies that bugs have this resolution
   comment(string):
      Comment for the bug
   template(string):
      File locally readable in the path specified
      used as a Template (passed the wi hash for values lookup)

:term:`Workitem` fields OUT

:Returns:
    result(boolean):
       True if everything was OK, False otherwise.


https://wiki.mozilla.org/index.php?title=Bugzilla:REST_API:Methods
"""

import re
from urllib2 import HTTPError
import datetime
import json

from Cheetah.Template import Template, NotFound

from boss.bz.xmlrpc import BugzillaXMLRPC
from boss.bz.rest import BugzillaREST


def prepare_comment(template, template_data):
    """Generate the comment to be added to the bug on bugzilla.

    :param template: Cheetah template
    :type template: string
    :param template_data: dictionary that contains the data items (refer workitem JSON hash description)
    :type template_data: dict
    """
    # Make a copy to avoid changing the parameter
    template_data = dict(template_data)
    template_data['time'] = datetime.datetime.ctime(datetime.datetime.today())
    try:
        text = unicode(Template(template, searchList=template_data))
    except NotFound:
        print "Template NotFound exception"
        print "#" * 79
        print template
        print "#" * 79
        print json.dumps(template_data, sort_keys=True, indent=4)
        print "#" * 79
        raise
    return text.encode('utf-8')


def format_bug_state(status, resolution):
    """Format a bug status and resolution for display.

    The formatting is the common one for bugzilla states:
    NEW, ASSIGNED, RESOLVED/DUPLICATE, CLOSED/FIXED, etc.
    If resolution is given but status is not, then there's no
    common way of writing it, and the function falls back on
    something like ?/FIXED to indicate that the status is unknown.

    :param status: Bug status
    :type status: string
    :param resolution: Bug resolution
    :type resolution: string
    """
    if not status:
        status = "?"
    if resolution:
        return "%s/%s" % (status, resolution)
    return str(status)


def really_handle_bug(bugzilla, bugnum, wid):
    """Act on one bug according to the workitem parameters.

    :param bugzilla: the configuration data from the config file
    :type bugzilla: dict
    :param bugnum: the number of the bug to be retrieved
    :type bugnum: string
    :param wid: the workitem object
    :type wid: object
    """
    iface = bugzilla['interface']
    bug = iface.bug_get(bugnum)

    expected_status = wid.params.check_status
    expected_resolution = wid.params.check_resolution

    if (expected_status and bug['status'] != expected_status) \
       or (expected_resolution and bug['resolution'] != expected_resolution):
        msg = "Bug %s %s is in state %s, expected %s" \
              % (bugzilla['name'], bugnum,
                 format_bug_state(bug['status'], bug['resolution']),
                 format_bug_state(expected_status, expected_resolution))
        print msg
        wid.fields.msg.append(msg)
        wid.result = False
        # Don't continue processing if bug is not in expected state
        return

    force_comment = False
    nbug = dict(id=bug['id'], token=bug['token'])

    if wid.params.status or wid.params.resolution:
        nbug['status'] = wid.params.status or bug['status']
        nbug['resolution'] = wid.params.resolution or bug['resolution']
        force_comment = True

    if wid.params.comment:
        comment = wid.params.comment
    elif wid.params.template:
        with open(wid.params.template) as fileobj:
            comment = prepare_comment(fileobj.read(), wid.to_h())
    elif bugzilla['template'] and force_comment:
        comment = prepare_comment(bugzilla["template"], wid.to_h())
    else:
        return

    nbug['comments'] = [{'text': comment}]
    iface.bug_update(nbug)


def handle_mentioned_bug(bugzilla, bugnum, wid):
    """Act on one bug according to the workitem parameters.

    Catch all exceptions because failure to handle a bug should not put
    the process in an error state. Return False if an exception was caught.

    :param bugzilla: the configuration data from the config file
    :type bugzilla: dict
    :param bugnum: the number of the bug to be retrieved
    :type bugnum: string
    :param wid: the workitem object
    :type wid: object
    """
    try:
        really_handle_bug(bugzilla, bugnum, wid)
        return True
    except HTTPError, exobj:
        print_http_debug(exobj)
        return False
    except Exception, exobj:
        print "Unexpected exception when handling bug %s: %s %s" \
              % (bugnum, exobj.__class__.__name__, str(exobj))
        return False


def print_http_debug(exobj):
    """ Helper utility function to pretty print an HTTP exception

    :param exobj: The exception
    :type exobj: HTTPError
    """
    print "-" * 60
    if hasattr(exobj, "code"):
        print exobj.code
    if hasattr(exobj, "read"):
        print exobj.read()
    if hasattr(exobj, "reason"):
        print exobj.reason()
    if hasattr(exobj, "headers"):
        print exobj.headers
    print "-" * 60


class ParticipantHandler(object):
    """ParticipantHandler object as defined by SkyNet API"""

    def __init__(self):
        self.bzs = None

    def handle_lifecycle_control(self, ctrl):
        """Participant control function.

            :param ctrl: The control object. If the message attribute is "start"
                         calls a function to parse the configuration and
                         retrieve a bugzilla authenitcation cookie which is kept
                         around for the lifetime of the script run
            :type ctrl: object
        """
        if ctrl.message == "start":
            self.setup_config(ctrl.config)
            # If there are any auth errors in the config, find out now.
            for bzconfig in self.bzs.values():
                bzconfig['interface'].login()

    def setup_config(self, config):
        """
        :param config: ConfigParser instance with the bugzilla configuration
        """
        supported_bzs = config.get("bugzilla", "bzs").split(",")
        self.bzs = {}

        for bz in supported_bzs:
            self.bzs[bz] = {}
            self.bzs[bz]['name'] = bz
            self.bzs[bz]['platforms'] = config.get(bz, 'platforms').split(',')
            self.bzs[bz]['regexp'] = config.get(bz, 'regexp')
            self.bzs[bz]['compiled_re'] = re.compile(config.get(bz, 'regexp'))
            self.bzs[bz]['method'] = config.get(bz, 'method')
            if self.bzs[bz]['method'] == 'REST':
                self.bzs[bz]['rest_slug'] = config.get(bz, 'rest_slug')
            self.bzs[bz]['server'] = config.get(bz, 'bugzilla_server')
            self.bzs[bz]['user'] = config.get(bz, 'bugzilla_user')
            self.bzs[bz]['password'] = config.get(bz, 'bugzilla_pwd')
            template = config.get(bz, 'comment_template')
            try:
                self.bzs[bz]['template'] = open(template).read()
            except:
                raise RuntimeError("Couldn't open %s" % template)

            method = self.bzs[bz]['method']
            if method == 'REST':
                self.bzs[bz]['interface'] = BugzillaREST(self.bzs[bz])
            elif method == 'XMLRPC':
                self.bzs[bz]['interface'] = BugzillaXMLRPC(self.bzs[bz])
            else:
                raise RuntimeError("Bugzilla method %s not implemented"
                                   % method)

    def handle_wi(self, wid):
        """Handle an incoming request for work as described in the workitem."""
        wid.result = False

        f = wid.fields

        if not f.msg:
            f.msg = []

        # Support both ev.actions and plain workitem
        if not f.ev or not f.ev.actions:
            if not f.relevant_changelog or not f.package:
                raise RuntimeError("Fields 'relevant_changelog' and 'package' "
                        "are mandatory when not handling a request")
            # Pack the flat workitem data bits into a fake actions array
            # so we can reuse the same code path
            actions = [{ "type": "submit",
                         "targetpackage" : f.package,
                         "relevant_changelog" : f.relevant_changelog }]
        else:
            actions = f.ev.actions

        # At this point all checks have passed.
        # The result can still become False if one of the verification
        # commands fails, but by default it's True.
        wid.result = True

        # Now handle all bugs mentioned in changelogs
        for action in actions:
            if action["type"] == "submit":
                self.handle_action(action, wid)

    def handle_action(self, action, wid):
        f = wid.fields
        package = action["targetpackage"]

        if "relevant_changelog" in action:
            chlog_entries = action["relevant_changelog"]
        else:
            return

        # Go through each bugzilla we support
        for (bugzillaname, bugzilla) in self.bzs.iteritems():
            # is this tracker used for this platform?
            if f.platform and f.platform not in bugzilla['platforms']:
                continue

            # Prepare bz data for the Templater
            f.bz = dict(bugs=[], failed_bugs=[], changed_bugs=[])

            # And then for each changelog deal with each bug mentioned
            for entry in chlog_entries:
                # Add this to the WI for the Templater
                f.bz.current_changlog_entry = entry
                for match in bugzilla['compiled_re'].finditer(entry):
                    bugnum = match.group('key')
                    if bugnum not in f.bz.bugs:
                        f.bz.bugs.append(bugnum)
                        if handle_mentioned_bug(bugzilla, bugnum, wid):
                            f.bz.changed_bugs.append(bugnum)
                        else:
                            f.bz.failed_bugs.append(bugnum)

            # Report on bugs.
            if f.bz.changed_bugs:
                msg = "Handled %s bugs %s " \
                      % (bugzillaname, ", ".join(f.bz.changed_bugs))
                print msg
                f.msg.append(msg)
            if f.bz.failed_bugs:
                msg = "Failed to properly deal with %s bugs %s" \
                       % (bugzillaname, ", ".join(f.bz.failed_bugs))
                print msg
                f.msg.append(msg)
            del f.as_dict()['bz']
