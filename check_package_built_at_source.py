#!/usr/bin/python
""" Quality check participant """

import json
from buildservice import BuildService

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

    def quality_check(self, wid):

        """ Quality check implementation """

        wid.result = False
        msg = wid.fields.msg if wid.field.msg else []
        actions = wid.fields.ev.actions
        targetrepo = wid.fields.targetrepo
        archs = wid.fields.archs
        archstring = ", ".join(archs)

        if not actions or not targetrepo or not archs:
            wid.set_field("__error__", "A needed field does not exist.")
            return

        result = True

        for action in actions:
            if not self.obs.isPackageSucceeded(action['sourceproject'],
                                               action['sourcepackage'],
                                               [targetrepo],
                                               archs):
                result = False
                msg.append("Package %s not built successfully in project %s \
                            repository %s for architectures %s \
                            " % (action['sourcepackage'],
                                 action['sourceproject'],
                                 targetrepo, archstring))


        wid.set_field("msg", msg)
        wid.result = result

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print json.dumps(wid.to_h(), sort_keys=True, indent=4)

        self.setup_obs(wid.namespace)
        self.quality_check(wid)
