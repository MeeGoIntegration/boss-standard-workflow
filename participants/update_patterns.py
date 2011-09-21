#!/usr/bin/python
""" Updates package patterns for a specific project as per package-groups
package updates

:term:`Workitem` fields IN:

:Parameters:
   project(string):
      project of which to update patterns to

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if the update was successfull

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
        self.setup_obs(wid.fields.namespace)
        