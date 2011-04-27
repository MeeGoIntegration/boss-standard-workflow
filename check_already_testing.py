#!/usr/bin/python
""" Quality check participant """

import sys, traceback
from buildservice import BuildService

try:
    import json
except ImportError:
    import simplejson as json

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

        result = True
        msg = [] if not wid.lookup("msg") else wid.lookup("msg")
        actions = wid.lookup('actions')
        #project = wid.lookup('project')
        #repository = wid.lookup('repository')
        #targetrepo = wid.lookup('targetrepo')
        #archs = wid.lookup('archs')
        #archstring = ", ".join(archs)

        in_testing = []

        for action in actions:
            # Check if packages are already in testing
            if not self.obs.hasChanges(action['sourceproject'],
                                      action['sourcepackage'],
                                      action['sourcerevision'],
                                      wid.lookup('test_project'),
                                      action['targetpackage']):
                in_testing.append(action['sourcepackage'])
                result = False

        if result :
            msg.append("Request packages not already under testing.")
        else:
            msg.append("The packages %s are already under testing in %s " \
                       % (" ".join(in_testing), wid.lookup('test_project')))
            wid.set_field("status","FAILED")


        wid.set_field("msg", msg)
        wid.set_result(result)

        return wid


    def handle_wi(self, wid):

        """ actual job thread """

        try:
            # We may want to examine the fields structure
            if 'debug_dump' in wid.fields():
                print json.dumps(wid.to_h(), sort_keys=True, indent=4)

            wid = self.quality_check(wid)

        except Exception as exp :
            print "Failed with exceptions %s " % exp
            wid.set_field("status","FAILED")
            traceback.print_exc(file=sys.stdout)
            wid.set_result(False)
        finally:
            print "Request #%s %s:\n%s" % (wid.lookup('rid'),
                                           wid.lookup('status'),
                                           "\n".join(wid.lookup('msg')))

