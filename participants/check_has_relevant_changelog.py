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


Check respects the values in [checks] section of packages boss.conf
for following keys:

    check_has_relevant_changelog:
        skip/warn this check

"""

from boss.checks import CheckActionProcessor

@CheckActionProcessor("check_has_relevant_changelog", action_idx=0, wid_idx=1)
def contains_relevant_changelog(action, _wid):
    """Check that action has relevan_changelog."""
    if "relevant_changelog" not in action:
        return False, "Package %s from project %s does not "\
                      "contain new changelog entries."\
                      % (action['sourcepackage'],
                         action['sourceproject'])
    return True, None


class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass

    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass

    def handle_wi(self, wid):
        """ actual job thread """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        actions = wid.fields.ev.actions

        if not actions:
            raise RuntimeError("Missing mandatory field 'ev.actions'")

        # skip requests marked as revert
        if "revert" in wid.fields.ev.description.lower():
            wid.result = True
            return

        result = True
        # Assert each package being submitted has relevant changelog entries.
        for action in actions:
            pkg_result, _ = contains_relevant_changelog(action, wid)
            result = result and pkg_result

        wid.result = result
