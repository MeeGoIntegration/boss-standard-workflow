#!/usr/bin/python
""" Checks that each entry in the actions array has been extended to contain
the relevant changelog entries introduced by this request.

.. warning::
   The get_relevant_changelog participant should have be run first to fetch
   the relevant changelog entries

:term:`Workitem` fields IN

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`.

:term:`Workitem` fields OUT

:Returns:
    result(Boolean):
       True if each action contain a "relevant_changelog" fields, False if any don't.

"""


class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass

    def quality_check(self, wid):

        """ Quality check implementation """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        actions = wid.fields.ev.actions

        if not actions:
            wid.fields.__error__ = "One of the mandatory fields: actions"\
                                   "does not exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field")

        result = True

        # Assert each package being submitted has relevant changelog entries.
        for action in actions:
            if not "relevant_changelog" in action:
                result = False
                wid.fields.msg.append("Package %s from project %s does not"\
                                      "contain new changelog entries."\
                                      % (action['sourcepackage'],
                                         action['sourceproject']))

        wid.result = result

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.quality_check(wid)
