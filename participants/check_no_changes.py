#!/usr/bin/python
""" Compares the checksums of each package named in a submit
(promotion) request to those of packages in their final destination if they
exist. Different checksums indicate the packages introduce changes.

:term:`Workitem` fields IN:

:Parameters:
   ev.actions(list):
      Request data structure :term:`actions`
      The participant only looks at submit actions

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean):
      True if all the submit actions in the request introduce changes
      Otherwise False

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
            wid.fields.msg =  []
        actions = wid.fields.ev.actions

        if not actions:
            raise RuntimeError("Missing mandatory field 'ev.actions'")

        self.setup_obs(wid.fields.ev.namespace)

        all_ok = True
        for action in actions:
            if action['type'] != 'submit':
                continue
            if not self.obs.hasChanges(action['sourceproject'],
                                       action['sourcepackage'],
                                       action['sourcerevision'],
                                       action['targetproject'],
                                       action['targetpackage']):
                wid.fields.msg.append(
                    "Package %(sourceproject)s %(sourcepackage)s"
                    " does not introduce any changes compared to"
                    " %(targetproject)s %(targetpackage)s" % action)
                all_ok = False

        wid.result = all_ok
