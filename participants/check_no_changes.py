#!/usr/bin/python
""" Compares the checksums of each package named in a submit
(promotion) request to those of packages in their final destination if they
exist. Different checksums indicate the packages introduce changes.

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      Request data structure :term:`actions`
      The participant only looks at submit actions

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if all the submit actions in the request introduce changes
      Otherwise False

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

        if not wid.fields.ev:
            raise RuntimeError("Missing mandatory field 'ev'")
        if not wid.fields.ev.namespace:
            raise RuntimeError("Missing mandatory field 'ev.namespace'")
        if not wid.fields.ev.actions:
            raise RuntimeError("Missing mandatory field 'ev.actions'")

        all_ok = True
        for action in wid.fields.ev.actions:
            if action['type'] != 'submit':
                continue
            if not self.obs.hasChanges(
                    action['sourceproject'],
                    action['sourcepackage'],
                    action['sourcerevision'],
                    action['targetproject'],
                    action['targetpackage']
            ):
                wid.fields.msg.append(
                    "Package %(sourceproject)s %(sourcepackage)s"
                    " does not introduce any changes compared to"
                    " %(targetproject)s %(targetpackage)s" % action)
                all_ok = False

        wid.result = all_ok
