#!/usr/bin/python
"""Checks that the submitter has the maintainer role in the originating project

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`
   ev.who:
      username is expected to be in the event namespace

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if the submitter is a maintainer, False otherwise.

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

        if not wid.fields.ev or not wid.fields.ev.actions:
            raise RuntimeError("Missing mandatory field 'ev.actions'")

        for action in wid.fields.ev.actions:
            if not self.obs.isMaintainer(action["sourceproject"],
                                         wid.fields.ev.who):
                wid.fields.status = "FAILED"
                wid.fields.msg.append(
                    "%s who submitted request %s from project %s "
                    "is not allowed to do so." % (
                        wid.fields.ev.who, wid.fields.ev.rid,
                        action["sourceproject"]
                    )
                )
                return

        wid.result = True
