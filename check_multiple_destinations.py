#!/usr/bin/python
""" Quality check participant """

import json

def multiple_dst_prj(actions):
    """ Check for multiple destinations """
    projects = []
    for action in actions:
        if action['targetproject'] not in projects:
            projects.append(action['targetproject'])
    if len(projects) != 1:
        return True
    else:
        return False

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
        msg = wid.fields.msg if wid.field.msg else []
        actions = wid.fields.ev.actions

        if not actions:
            wid.set_field("__error__", "A needed field does not exist.")
            return

        if multiple_dst_prj(actions):
            msg.append('Multiple destination projects in request')
        else:
            wid.result = True

        wid.set_field("msg", msg)

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if 'debug_dump' in wid.fields() or 'debug_dump' in wid.params():
            print json.dumps(wid.to_h(), sort_keys=True, indent=4)

        self.quality_check(wid)
