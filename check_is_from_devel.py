#!/usr/bin/python
""" Quality check participant """

import re

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
        msg = wid.fields.msg if wid.fields.msg else []
        actions = wid.fields.ev.actions
        reg_exp = wid.params.regexp

        if not actions or not reg_exp:
            wid.set_field("__error__", "A needed field does not exist.")
            return

        result = True

        # assert packages are being submitted from a project that matches the
        # devel area regexp provided

        for action in actions:
            test_match = re.match(reg_exp, action["sourceproject"])
            if not test_match or \
               not test_match.group(0) == action["sourceproject"]:
                result = False
                msg.append("Source project %s does not match the \
                            development area %s" % (action["sourceproject"],
                                                    reg_exp))

        wid.set_field("msg", msg)
        wid.result = result

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.quality_check(wid)
