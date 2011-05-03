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
        email = wid.fields.email if wid.fields.email else []
        who = wid.fields.ev.who

        if not who:
            wid.set_field("__error__", "A needed field does not exist.")
            return

        user_email = self.obs.getUserEmail(who)

        if user_email:
            email.append(user_email)
            wid.set_field("email", email)
            wid.result = True
            return
        else:
            msg.append("User %s doesn't have an email recorded" % who)

        wid.set_field("msg", msg)

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print json.dumps(wid.to_h(), sort_keys=True, indent=4)

        self.setup_obs(wid.namespace)
        self.quality_check(wid)
