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
        msg = wid.fields.msg if wid.field.msg else []
        actions = wid.fields.ev.actions

        if not actions:
            wid.set_field("__error__", "A needed field does not exist.")
            return


        for action in actions:
            if self.obs.hasChanges(action['sourceproject'],
                                   action['sourcepackage'],
                                   action['sourcerevision'],
                                   action['targetproject'],
                                   action['targetpackage']):
                wid.result = True
                return

        msg.append("None of the packages in this request introduce \
                    source changes compared to \
                    %s" % (actions[0]['targetproject']))

        wid.set_field("msg", msg)

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.setup_obs(wid.namespace)
        self.quality_check(wid)
