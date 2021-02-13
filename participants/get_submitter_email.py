#!/usr/bin/python
""" Participant to get a person's email from an OBS instance.

    *Workitem fields IN :*

    :param ev.who: username is expected to be in the event namespace
    :type ev.who: string

    *Workitem fields OUT :*

    :returns mail_to: appends user's email to the email recipient list
    :rtype mail_to: list of strings

"""

from boss.obs import BuildServiceParticipant


class ParticipantHandler(BuildServiceParticipant):
    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass

    @BuildServiceParticipant.setup_obs
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

        user_email = self.obs.getUserEmail(who)

        if user_email:
            wid.fields.mail_to.append(user_email)
            wid.result = True
        else:
            wid.fields.msg.append("User %s doesn't have an email" % who)
