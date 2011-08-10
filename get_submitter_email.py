#!/usr/bin/python
""" Participant to get a person's email from an OBS instance.
    
    *Workitem fields IN :*

    :param ev.who: username is expected to be in the event namespace 
    :type ev.who: string

    *Workitem fields OUT :*

    :returns email: appends user's email to the email list
    :rtype email: list of strings

"""

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
        if not wid.fields.msg:
            wid.fields.msg = []
        if not wid.fields.email:
            wid.fields.email = []
        who = wid.fields.ev.who

        if not who:
            wid.fields.__error__ = "One of the mandatory fields: who"\
                                   "does not exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field")

        user_email = self.obs.getUserEmail(who)

        if user_email:
            wid.fields.email.append(user_email)
            wid.result = True
        else:
            wid.fields.msg.append("User %s doesn't have an email" % who)


    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.setup_obs(wid.namespace)
        self.quality_check(wid)
