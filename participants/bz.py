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

from collections import defaultdict
from Cheetah.Template import Template, NotFound

from boss.bz.xmlrpc import BugzillaXMLRPC
from boss.bz.rest import BugzillaREST, BugzillaError

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

def prepare_comment(template, template_data):
    """Generate the comment to be added to the bug on bugzilla.

    :param template: Cheetah template
    :type template: string
    :param template_data: dictionary that contains the data items (refer workitem JSON hash description)
    :type template_data: dict
    """
    # Make a copy to avoid changing the parameter
    searchlist = {'f': general_map(template_data,
                                   dicts=ForgivingDict, values=fixup_utf8)}
    searchlist['req'] = searchlist['f']['req'] or ForgivingDict()

    searchlist['time'] = datetime.datetime.ctime(datetime.datetime.today())
    try:
        text = unicode(Template(template, searchList=searchlist))
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


def handle_mentioned_bug(bugzilla, bugnum, wid):
    """Act on one bug according to the workitem parameters.
    Return True iff the bug was updated.

    :param bugzilla: the configuration data from the config file
    :type bugzilla: dict
    :param bugnum: the number of the bug to be retrieved
    :type bugnum: string
    :param wid: the workitem object
    :type wid: object
    """
    iface = bugzilla['interface']
    try:
        bug = iface.bug_get(bugnum)
    except BugzillaError, error:
        if error.code == 101:
            msg = "Bug %s %s not found"
            print msg
            wid.fields.msg.append(msg)
            wid.result = False
            return False
        raise

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
        return False

    force_comment = False
    print bugnum
    print bug
    nbug = dict(id=bug['id'], update_token=bug['update_token'])

    if wid.params.status or wid.params.resolution:
        nbug['status'] = wid.params.status or bug['status']
        nbug['resolution'] = wid.params.resolution or bug['resolution']
        force_comment = True

    if wid.params.comment:
        comment = wid.params.comment
    elif wid.params.template:
        with open(wid.params.template) as fileobj:
            comment = prepare_comment(fileobj.read(), wid.fields.as_dict())
    elif bugzilla['template']:
        comment = prepare_comment(bugzilla["template"], wid.fields.as_dict())
    else:
        return False

    nbug['comment'] = {'comment': comment}
    iface.bug_update(nbug)
    return True


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
        msgs = []
        for action in actions:
            if action["type"] == "submit":
                msgs.extend(self.handle_action(action, wid))

        # Add the messages only at the end, so that when comments are
        # left on multiple bugzillas they are not polluted with messages
        # about earlier bugzillas.
        f.msg.extend(msgs)

    def handle_action(self, action, wid):
        """Handle a single submit action from an incoming request.
        Return the list of messages to be added when all processing is done."""
        f = wid.fields
        package = action["targetpackage"]
        msgs = []

        if "relevant_changelog" in action:
            chlog_entries = action["relevant_changelog"]
        else:
            return msgs

        # Go through each bugzilla we support
        for (bugzillaname, bugzilla) in self.bzs.iteritems():
            # is this tracker used for this platform?
            if f.platform and f.platform not in bugzilla['platforms']:
                continue

            bugs = []
            updated_bugs = []

            # And then for each changelog deal with each bug mentioned
            for entry in chlog_entries:
                # Add this to the WI for the Templater
                f.bz = dict(current_changlog_entry=entry)
                for match in bugzilla['compiled_re'].finditer(entry):
                    bugnum = match.group('key')
                    if bugnum not in bugs:
                        bugs.append(bugnum)
                        if handle_mentioned_bug(bugzilla, bugnum, wid):
                            updated_bugs.append(bugnum)

            if bugs:
                print "Checked %s bugs %s" % (bugzillaname, ", ".join(bugs))
            if updated_bugs:
                msg = "Updated %s bugs %s" \
                      % (bugzillaname, ", ".join(updated_bugs))
                print msg
                msgs.append(msg)
            del f.as_dict()['bz']
        return msgs
