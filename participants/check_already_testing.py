#!/usr/bin/python3
""" This participant compares the checksums of each package named in a submit
(promotion) request to those of packages in the testing area if they exist.
Different checksums indicate the packages are not in the testing area.

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      submit request data structure :term:`actions`

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if no packages are already in testing, False if a package was already
      found in testing

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
        rid = wid.fields.ev.rid
        actions = wid.fields.ev.actions
        test_project = wid.fields.test_project

        if not rid or not actions or not test_project:
            raise RuntimeError("Missing one of the mandatory fields 'ev.rid', "
                    "'ev.actions' or 'test_project'")

        self.setup_obs(wid.fields.ev.namespace)

        in_testing = []
        message = ""

        for action in actions:
            if action['type'] != "submit":
                continue
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
            wid.fields.status = "FAILED"

        wid.fields.msg.append(message)
