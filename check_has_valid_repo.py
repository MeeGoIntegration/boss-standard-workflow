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
   
    def get_target_repo(self, prj, target_project, target_repository,
                      target_archs):
        """ Find a repo that builds only against one target for certain 
            archs """

        target = "%s/%s" % (target_project, target_repository)
        prj_repos = self.obs.getProjectRepositories(prj)
        if prj_repos:
            for repo in prj_repos:
                repo_targets = self.obs.getRepositoryTargets(prj, repo)
                if len(repo_targets == 1 ):
                    if target in repo_targets:
                        repo_archs = self.obs.getRepositoryArchs(prj, repo)
                        if set(target_archs).issubset(repo_archs):
                            return repo
        return False

    def quality_check(self, wid):

        """ Quality check implementation """

        wid.result = False
        if not wid.fields.msg:
            wid.fields.msg = []
        actions = wid.fields.ev.actions
        project = wid.fields.project
        repository = wid.fields.repository
        archs = wid.fields.archs
        archstring = ", ".join(archs)

        if not actions or not project or not repository or not archs:
            wid.fields.__error__ = "One of the mandatory fields: actions, "\
                                   "project, repository and archs does not"\
                                   "exist."
            wid.fields.msg.append(wid.fields.__error__)
            raise RuntimeError("Missing mandatory field")

        # Assert existence and get target repo of interest.
        targetrepo = self.get_target_repo(actions[0]['sourceproject'],
                                          project, repository, archs)

        if not targetrepo:
            wid.fields.msg.append("Project %s does not contain a repository"\
                                  "that builds only against project %s "\
                                  "repository %s for architectures %s" % \
                                  (actions[0]['sourceproject'],
                                   project, repository ,
                                   archstring))
        else:
            wid.targetrepo = targetrepo
            wid.result = True
            wid.fields.msg.append("Target repo %s found." % targetrepo)

    def handle_wi(self, wid):

        """ actual job thread """

        # We may want to examine the fields structure
        if wid.fields.debug_dump or wid.params.debug_dump:
            print wid.dump()

        self.setup_obs(wid.namespace)
        self.quality_check(wid)
