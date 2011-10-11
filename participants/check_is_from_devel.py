#!/usr/bin/python
""" assert packages are being submitted from a project that matches the
devel area regexp provided.

:term:`Workitem` fields IN

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`.

:term:`Workitem` params IN

:Parameters:
   reg_exp(string):
      a regular expression string

:term:`Workitem` fields OUT

:Returns:
    result(Boolean):
       True if source projects match the regexp, False if any don't.


Check respects the values in [checks] section of packages boss.conf
for following keys:

    check_is_from_devel:
        skip/warn this check

"""

import re
from boss.checks import CheckActionProcessor

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass
    
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass
    
    @CheckActionProcessor("check_is_from_devel")
    def _source_matches(self, action, _wid, pattern):
        test_match = pattern.match(action["sourceproject"])
        if not test_match or \
                not test_match.group(0) == action["sourceproject"]:
            return False, "Source project %s does not match the"\
                    " development area" % action["sourceproject"]
        return True, None

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        actions = wid.fields.ev.actions
        reg_exp = wid.params.regexp

        if not actions or not reg_exp:
            wid.fields.__error__ = "One of the mandatory fields: actions or "\
                                   "parameters: regexp does not exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field")

        pattern = re.compile(reg_exp)

        result = True

        for action in actions:
            pkg_result, _ = self._source_matches(action, wid, pattern)
            result = result and pkg_result

        wid.result = result
