#!/usr/bin/python
""" Quality check participant """

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
        if not wid.fields.msg:
            wid.fields.msg = []
        actions = wid.fields.ev.actions

        if not actions:
            wid.fields.__error__ = "One of the mandatory fields: actions"\
                                   "does not exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field")

        if multiple_dst_prj(actions):
            wid.fields.msg.append('Multiple destination projects in request')
        else:
            wid.result = True

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.quality_check(wid)
