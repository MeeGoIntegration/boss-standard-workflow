#!/usr/bin/python
""" Participant to get a person's email from an OBS instance.

    *Workitem fields IN :*

    :param ev.who: username is expected to be in the event namespace
    :type ev.who: string

    *Workitem fields OUT :*

    :returns mail_to: appends user's email to the email recipient list
    :rtype mail_to: list of strings

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


    def handle_wi(self, wid):
        """ actual job thread """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        if not wid.fields.mail_to:
            wid.fields.mail_to = []

        if not wid.fields.ev or not wid.fields.ev.who:
            raise RuntimeError("Missing mandatory field 'ev.who'")
        who = wid.fields.ev.who

        self.setup_obs(wid.fields.ev.namespace)

        user_email = self.obs.getUserEmail(who)

        if user_email:
            wid.fields.mail_to.append(user_email)
            wid.result = True
        else:
            wid.fields.msg.append("User %s doesn't have an email" % who)
