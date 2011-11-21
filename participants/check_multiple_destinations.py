#!/usr/bin/python
""" Checks that there aren't multiple destination in the actions array of this
request.

:term:`Workitem` fields IN

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`.

:term:`Workitem` fields OUT

:Returns:
    result(Boolean):
       True if each actions contain multiple destinations, False otherwise.

"""


def multiple_dst_prj(actions):
    """ Check for multiple destinations """
    projects = []
    for action in actions:
        target = action['targetproject'] or action['deleteproject']
        if target not in projects:
            projects.append(target)
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
    
    def handle_wi(self, wid):
        """ actual job thread """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        actions = wid.fields.ev.actions

        if not actions:
            raise RuntimeError("Missing mandatory field 'ev.actions'")

        if multiple_dst_prj(actions):
            wid.fields.msg.append('Multiple destination projects in request')
        else:
            wid.result = True
