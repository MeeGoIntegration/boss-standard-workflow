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
        msg = wid.fields.msg if wid.fields.msg else []
        actions = wid.fields.ev.actions

        if not actions:
            wid.__error__ = "'ev.actions' field is needed and is not in workitem."
            return

        for action in actions:
            if not self.obs.isMaintainer(action["sourceproject"],
                                         wid.fields.ev.who):
                msg.append("Request from project %s by %s who is not a maintainer" \
                           % (action["sourceproject"], wid.fields.ev.who))
                wid.fields.msg = msg
                return

        wid.result = True

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.setup_obs(wid.fields.ev.namespace)
        self.quality_check(wid)
