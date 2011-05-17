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
        actions = wid.fields.ev.actions

        # Now check the prereq proces fields
        targetrepo = wid.fields.targetrepo
        archs = wid.fields.archs
        archstring = ", ".join(archs)

        if not actions or not targetrepo or not archs:
            wid.fields.__error__ = "check_package_built_at_source needs all of"\
                                   ": ev.actions, targetrepo and archs in the "\
                                   "workitem."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field") 

        # All good unless any of the targets fail
        result = True
        for action in actions:
            for arch in archs:
                if not self.obs.isPackageSucceeded(action['sourceproject'],
                                                   [targetrepo],
                                                   action['sourcepackage'],
                                                   arch):
                    result = False
                    wid.fields.msg.append("Package %s not built successfully"\
                                          "in project %s repository %s for"\
                                          "architectures %s"\
                                          % (action['sourcepackage'],
                                             action['sourceproject'],
                                             targetrepo, archstring))


        wid.result = result

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.setup_obs(wid.fields.ev.namespace)
        self.quality_check(wid)
