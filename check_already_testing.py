#!/usr/bin/python
""" Quality check participant """

import json
from buildservice import BuildService

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = BuildService()

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass
    
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass
    
    def quality_check(self, wid):

        """ Quality check implementation """

        wid.set_result(False)
        msg = wid.fields.msg if wid.field.msg else []
        rid = wid.fields.ev.rid
        actions = wid.fields.ev.actions
        test_project = wid.fields.test_project

        if not rid or not actions or not test_project:
            return

        in_testing = []
        message = ""

        for action in actions:
            # Check if packages are already in testing
            if not self.obs.hasChanges(action['sourceproject'],
                                      action['sourcepackage'],
                                      action['sourcerevision'],
                                      test_project,
                                      action['targetpackage']):
                in_testing.append(action['sourcepackage'])

        if not in_testing:
            message = "Request %s packages not already under testing." % rid
            wid.set_result(True)
        else:
            message = "Request %s packages %s are already under testing in \
                        %s" % (rid, " ".join(in_testing), 
                               wid.lookup('test_project'))

        msg.append(message)
        wid.set_field("msg", msg)

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if 'debug_dump' in wid.fields() or 'debug_dump' in wid.params():
            print json.dumps(wid.to_h(), sort_keys=True, indent=4)

        self.quality_check(wid)
