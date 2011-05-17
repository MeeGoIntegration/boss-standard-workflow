#!/usr/bin/python
""" Quality check participant """

from buildservice import BuildService

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = None
        self.oscrc = None

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass
    
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        if ctrl.message == "start":
            if ctrl.config.has_option("obs", "oscrc"):
                self.oscrc = ctrl.config.get("obs", "oscrc")
    
    def setup_obs(self, namespace):
        """ setup the Buildservice instance using the namespace as an alias
            to the apiurl """

        self.obs = BuildService(oscrc=self.oscrc, apiurl=namespace)

    def quality_check(self, wid):

        """ Quality check implementation """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        rid = wid.fields.ev.rid
        actions = wid.fields.ev.actions
        test_project = wid.fields.test_project

        if not rid or not actions or not test_project:
            wid.fields.__error__ = "One of the mandatory fields: rid, actions"\
                                   "and test_project does not exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field") 


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
            wid.result = True
        else:
            message = "Request %s packages %s are already under testing in \
                        %s" % (rid, " ".join(in_testing), 
                               test_project)

        wid.fields.msg.append(message)

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump() 

        self.setup_obs(wid.namespace)
        self.quality_check(wid)
