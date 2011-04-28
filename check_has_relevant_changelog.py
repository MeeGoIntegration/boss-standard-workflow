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
        #archs = wid.lookup('archs')
        #archstring = ", ".join(archs)

        # Assert each package being submitted has relevant changelog entries.
        for action in actions:
            if not "relevant_changelog" in action:
                wid.set_field("status","FAILED")
                msg.append("Package %s from project %s does not contain new \
                            changelog entries compared to package %s in \
                            project %s" % (action['sourcepackage'],
                                           action['sourceproject'],
                                           action['targetpackage'],
                                           action['targetproject']))
                result = False

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

