#!/usr/bin/python
""" Looks at the build status of the packages being submitted in a certain repo
and for certain architectures, and checks if they are built successfuly

.. warning::
   The check_has_valid_repo participant should have be run first to identify
   the correct repository used for checking.

:term:`Workitem` fields IN :

:Parameters:
   ev.actions(list):
      the request :term:`actions`
   targetrepo(string):
      The name of the repository that satisfied the requirements
   archs(list):
      the architectures we care about (i586, armv7l etc..)

:term:`Workitem` fields OUT :

:Returns:
   result(Boolean):
      True if the needed repository was found, False otherwise

Check respects the skip/warn values in [checks] section of packages boss.conf
for following keys:

    check_package_built_at_source:
        skip/warn for all package build checks

"""

from buildservice import BuildService
from boss.checks import CheckActionProcessor
from urllib2 import HTTPError

def workitem_error(workitem, msg):
    """Convenience function for reporting unlikely errors."""
    if not workitem.fields.msg:
        workitem.fields.msg = []
    workitem.error = "[%s] %s" % (workitem.participant_name, msg)
    workitem.fields.msg.append(workitem.error)
    raise RuntimeError(workitem.error)

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = None
        self.oscrc = None

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")

    def setup_obs(self, namespace):
        """ setup the Buildservice instance using the namespace as an alias
            to the apiurl """

        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)
    
    @CheckActionProcessor("check_package_built_at_source")
    def quality_check(self, action, _wid):

        """ Quality check implementation """

        result = True
        message = None
        failed_archs = []
        _plural = ""

        for arch in _wid.fields.archs:
            try:
                if not self.obs.isPackageSucceeded(action['sourceproject'],
                                               _wid.fields.targetrepo,
                                               action['sourcepackage'],
                                               arch):
                    result = False
                    failed_archs.append(arch)
            except HTTPError, exc:
                if exc.code == 404:
                    result = False
                    failed_archs.append(arch)
                else:
                    raise

        if not result:
            _plural = ""
            if len(failed_archs) > 1:
                _plural = "s"
            message = "Package %s not built in project %s against repository"\
                      " %s for architecture%s %s" % (action['sourcepackage'],
                                                     action['sourceproject'],
                                                     _wid.fields.targetrepo,
                                                     _plural,
                                                     ",".join(failed_archs))


        return result, message

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        # Now check the prereq process fields
        if not wid.fields.ev.actions:
            workitem_error(wid, "need ev.actions")
        if not wid.fields.targetrepo:
            workitem_error(wid, "need targetrepo")
        if not wid.fields.archs:
            workitem_error(wid, "need archs")

        self.setup_obs(wid.fields.ev.namespace)

        for action in wid.fields.ev.actions:
            self.quality_check(action, wid)

