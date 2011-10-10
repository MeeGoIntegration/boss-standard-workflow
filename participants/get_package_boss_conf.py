"""
Retrieves and parses boss.conf files for packages in the submit request

Package in OBS can contain a file named boss.conf, which uses the ini-style
format. The configuration file is parsed and the key value pairs are stored in
the workitem.

For example if package 'helloworld' is part of the requests and has boss.conf
file with following contents::

    [checks]
    check_package_is_complete = warn
    check_mentions_bug = skip

It would result in workitem field structure::

    "package_conf": {
        "helloworld": {
            "checks": {
                "check_package_is_complete": "warn",
                "check_mentions_bug": "skip"
                }
            }
        }

The possible configuration values will be documented by the participants that
use them.

For sumbit actions the boss.conf is fetched from the package in source project
and for delete actions it is fetched from the package to be deleted.

:term:`Workitem` fields IN

:Parameters:
   ev.actions(list):
      Submit request data structure :term:`actions`.
   ev.namespace:
      OBS namespace

:term:`Workitem` fields OUT :

:Returns:
   result(boolean):
      True if successfully parsed the bosslintrc files, othewise False
   package_conf(dictionary):
      Configuration dictionaries for each package

"""

from ConfigParser import ConfigParser
from StringIO import StringIO
from urllib2 import HTTPError
from buildservice import BuildService

class ParticipantHandler(object):
    """ Class implementation as required by the API"""

    def __init__(self):
        self.oscrc = None
        self.obs = None

    def handle_lifecycle_control(self, ctrl):
        """Participant lifecycle control."""
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")

    def handle_wi(self, wid):
        """Participant workitem handler."""

        wid.result = False
        if wid.params.debug_dump or wid.fields.debug_dump:
            print wid.dump()
        if not wid.fields.msg:
            wid.fields.msg = []

        if not wid.fields.ev:
            raise RuntimeError("Mandatory field 'ev' missing")
        if not wid.fields.ev.actions:
            raise RuntimeError("Mandatory field 'ev.actions' missing")
        if not wid.fields.ev.namespace:
            raise RuntimeError("Mandatory field 'ev.namespace' missing")

        wid.fields.package_conf = {}
        # We need direct access to the dictionary as DictAttrProxy does not
        # have __getitem__
        package_conf = wid.fields.package_conf.as_dict()

        self._setup_obs(wid.fields.ev.namespace)

        for action in wid.fields.ev.actions:
            self._process_action(action, package_conf)
        wid.result = True

    def _setup_obs(self, namespace):
        """Initialize buildservice instance."""
        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    def _get_boss_conf(self, project, package, revision=None):
        """Fetch boss.conf contents for package.

        :returns: boss.conf contents as string or None if package does not have
            boss.conf
        """
        try:
            contents = self.obs.getFile(
                    project, package, "boss.conf", revision)
        except HTTPError, exobj:
            if exobj.getcode() == 404:
                # Package does not have boss.conf
                contents = None
            else:
                # something else failed on OBS
                raise
        except Exception:
            # buildservice raises all kinds of weird exceptions
            print "Failed to get boss.conf for %s %s revision %s" % \
                    (project, package, revision)
            raise
        return contents


    def _process_action(self, action, package_conf):
        """Process single action from event action list.

        Gets package boss.conf, parses it and puts the result in
        package_conf[package_name]
        """
        package = action.get("sourcepackage", None)\
                or action.get("deletepackage", None)
        if not package:
            # This is not package related action
            return

        # In theory sourcepackage and targetpackage can have different names,
        # but we don't support that.

        # Guarantee fields.package_conf.<package name> for all packages in
        # request, even if it is empty.
        package_conf[package] = {}

        if action["type"] == "submit":
            contents = self._get_boss_conf(
                    action["sourceproject"], action["sourcepackage"],
                    action["sourcerevision"]) or ""
        elif action["type"] == "delete":
            contents = self._get_boss_conf(
                    action["deleteproject"], action["deletepackage"]) or ""
        else:
            print "Unknown action type '%s'" % action["type"]
            return

        conf = ConfigParser()
        conf.readfp(StringIO(contents))
        for section in conf.sections():
            # Create config sections under package
            package_conf[package][section] = {}
            for key, value in conf.items(section):
                # Read key - value pairs in sections
                package_conf[package][section][key] = value

