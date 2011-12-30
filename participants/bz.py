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

import re, os
import urllib2
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
    template_data['time'] = datetime.datetime.ctime(datetime.datetime.today())
    try:
        text = Template(template, searchList=template_data)
    except NotFound:
        print "Template NotFound exception"
        print "#" * 79
        print template
        print "#" * 79
        print json.dumps(template_data, sort_keys=True, indent=4)
        print "#" * 79
        raise

    comment = {"text": str(text)}
    return comment

def bz_opener(bugzilla, url, method=None, data=None):
    """This is where the HTTP communication with the bugzilla REST API happens.
    
    :param bugzilla: the configuration data structure constructed from the config file
    :type bugzilla: dict
    :param url: the constructed REST API call
    :type url: string
    :param method: HTTP method to override the default POST/GET, to support PUT
    :type method: string
    :param data: The REST API call JSON data used in a POST request
    :type data: object
    """
    uri = bugzilla['bugzilla_server'] + bugzilla['rest_slug']
    user = bugzilla['bugzilla_user']
    passwd = bugzilla['bugzilla_pwd']

    pwmgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    pwmgr.add_password(realm=None, uri=uri, user=user, passwd=passwd)
    auth_handler = urllib2.HTTPBasicAuthHandler(pwmgr)

    opener = urllib2.build_opener(auth_handler)
    opener.addheaders = [
        ('Content-Type', 'application/json'),
        ('Accept', 'application/json'),
        ]

    if "Bugzilla_login" in bugzilla['cookies']:
        print "Old url %s" % url
        url = (url + "?userid="
               + bugzilla['cookies']['Bugzilla_login']
               + "&cookie="
               + bugzilla['cookies']['Bugzilla_logincookie'])
        print "New url %s" % url

    if not data:
        return json.loads(opener.open(uri + url).read())
    else:
        req = urllib2.Request(uri + url, data = json.dumps(data))
        req.add_header('Content-Type', 'application/json')
        req.add_header('Accept', 'application/json')
        if method:
            req.get_method = lambda: method
        return json.loads(opener.open(req).read())

def get_bug(bugzilla, bugid):
    """Makes a bugzilla REST API call to get a bug.

    :param bugzilla:  the configuration data structure constructed from the config file
    :type bugzilla: dict
    :param bugid: the number of the bug to be retrieved
    :type bugid: string
    """
    return bz_opener(bugzilla, 'bug/%s' % bugid)

def put_bug(bugzilla, bugid, bug):
    """Makes a bugzilla REST API call to modify a bug.

    :param bugzilla:  the configuration data structure constructed from the config file
    :type bugzilla: dict
    :param bugid: the number of the bug to be retrieved
    :type bugid: string
    :param bug: the modified bug data object
    :type bugid: object
    """
    return bz_opener(bugzilla, 'bug/%s' % bugid, method="PUT", data=bug)

def bz_state_comment(bugzilla, bugnum, status, resolution, wid):
    """Get a bug object, modify it as specified and then save it to bugzilla.

    :param bugzilla:  the configuration data structure constructed from the config file
    :type bugzilla: dict
    :param bugnum: the number of the bug to be retrieved
    :type bugnum: string
    :param status: the new status to be set
    :type status: string
    :param resolution: the new resolution to be set
    :type statuts: string
    :param wid: the workitem object
    :type wid: object
    """
    if bugzilla['method'] != 'REST':
        print "Not implemented"
        return False

    bug = get_bug(bugzilla, bugnum)

    comment = ""
    if wid.params.comment:
        comment = {"text": str(wid.params.comment)}
    elif wid.params.template and os.path.isfile(wid.params.template):
        with open(wid.params.template) as fileobj:
            comment = prepare_comment(fileobj.read(), wid.to_h())
    else:
        comment = prepare_comment(bugzilla["template"], wid.to_h())

    nbug = {}
    if "version" in bugzilla and bugzilla['version'] == '0.8':
        # old version of REST API
        token_name = 'token'
    else:
        token_name = 'update_token'
    if token_name in bug:
        nbug['token'] = bug[token_name]
    else:
        print "This isn't going to work...."

    # Initially set to the original status and resolution
    if "status" in bug:
        nbug['status'] = bug['status']
    if "resolution" in bug:
        nbug['resolution'] = bug['resolution']

    # and if new ones are specified, set them
    if status:
        nbug['status'] = status
    if resolution:
        nbug['resolution'] = resolution

    nbug["comments"] = [comment]
    #year, week, day = datetime.date.isocalendar(datetime.datetime.today())
    #milestone = "%d-%02d" % (year, week)
    #nbug["target_milestone"] = milestone
    result = put_bug(bugzilla, bugnum, nbug)
    # FIXME: use result
    return True


def get_bug_attr(bugzilla, bugnum, attr):
    """Get a bug attribute.

    :param bugzilla:  the configuration data structure constructed from the config file
    :type bugzilla: dict
    :param bugnum: the number of the bug to be retrieved
    :type bugnum: string
    :param attr: the name of an attribute whose value is needed
    :type attr: string
    """
    if bugzilla['method'] != 'REST':
        print "Not implemented"
        return None
    bug = get_bug(bugzilla, bugnum)
    if attr in bug.keys():
        return bug[attr]
    else:
        return None

def handle_mentioned_bug(bugzilla, bugnum, wid):
    """Act on one bug according to the workitem parameters.

    :param bugzilla: the configuration data from the config file
    :type bugzilla: dict
    :param bugnum: the number of the bug to be retrieved
    :type bugnum: string
    :param wid: the workitem object
    :type wid: object
    """
    try:
        status = wid.params.status
        resolution = wid.params.resolution
        return bz_state_comment(bugzilla, bugnum, status, resolution, wid)
    except HTTPError, exobj:
        print_http_debug(exobj)
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
            self.bzs[bz]['platforms'] = config.get(bz, 'platforms').split(',')
            self.bzs[bz]['regexp'] = config.get(bz, 'regexp')
            self.bzs[bz]['compiled_re'] = re.compile(config.get(bz, 'regexp'))
            self.bzs[bz]['method'] = config.get(bz, 'method')
            self.bzs[bz]['rest_slug'] = config.get(bz, 'rest_slug', None)
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
        if wid.params.comment or wid.params.template:
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
