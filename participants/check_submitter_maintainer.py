#!/usr/bin/python
""" Checks that the submitter has the maintainer role in the originating project

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`
   ev.who:
      username is expected to be in the event namespace

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if the submitter is a maintainer, False otherwise.

"""


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


    def handle_wi(self, wid):
        """ actual job thread """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        actions = wid.fields.ev.actions

        if not actions:
            wid.fields.__error__ = "Mandatory field: actions does not exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field")

        self.setup_obs(wid.fields.ev.namespace)

        for action in actions:
            if not self.obs.isMaintainer(action["sourceproject"],
                                         wid.fields.ev.who):
                wid.fields.status = "FAILED"
                wid.fields.msg.append("%s who submitted request %s "\
                                      "from project %s is not allowed to do "\
                                      "so." % (wid.fields.ev.who,
                                               wid.fields.ev.rid,
                                               action["sourceproject"]))
                return

        wid.result = True
