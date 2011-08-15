#!/usr/bin/python
""" Compares the checksums of each package named in a submit
(promotion) request to those of packages in their final destination if they 
exist. Different checksums indicate the packages introduce changes. 

:term:`Workitem` fields IN:

:Parameters: 
   ev.actions(list):
      submit request data structure :term:`actions`

:term:`Workitem` fields OUT:

:Returns:
   result(Boolean): 
      False if no packages are differnet, True if at least one is different

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

    def quality_check(self, wid):

        """ Quality check implementation """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg =  []
        actions = wid.fields.ev.actions

        if not actions:
            wid.fields.__error__ = "One of the mandatory fields: actions"\
                                   "does not exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field")

        for action in actions:
            if self.obs.hasChanges(action['sourceproject'],
                                   action['sourcepackage'],
                                   action['sourcerevision'],
                                   action['targetproject'],
                                   action['targetpackage']):
                wid.result = True
                return

        wid.fields.msg.append("None of the packages in this request introduce"\
                              "source changes compared to %s" % \
                               (actions[0]['targetproject']))

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.setup_obs(wid.ev.namespace)
        self.quality_check(wid)
