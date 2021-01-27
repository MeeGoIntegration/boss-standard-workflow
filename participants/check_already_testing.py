#!/usr/bin/python
""" This participant compares the checksums of each package named in a submit
(promotion) request to those of packages in the testing area if they exist.
Different checksums indicate the packages are not in the testing area.

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if no packages are already in testing, False if a package was
      already found in testing

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
        rid = wid.fields.ev.rid
        actions = wid.fields.ev.actions
        test_project = wid.fields.test_project

        if not rid or not actions or not test_project:
            raise RuntimeError(
                "Missing one of the mandatory fields 'ev.rid', "
                "'ev.actions' or 'test_project'"
            )

        in_testing = []
        message = ""

        for action in actions:
            if action['type'] != "submit":
                continue
            # Check if packages are already in testing
            if not self.obs.hasChanges(
                    action['sourceproject'],
                    action['sourcepackage'],
                    action['sourcerevision'],
                    test_project,
                    action['targetpackage']
            ):
                in_testing.append(action['sourcepackage'])

        if not in_testing:
            message = "Request %s packages not already under testing." % rid
            wid.result = True
        else:
            message = "Request %s packages %s already under testing in %s" % (
                rid, " ".join(in_testing), test_project)
            wid.fields.status = "FAILED"

        wid.fields.msg.append(message)
