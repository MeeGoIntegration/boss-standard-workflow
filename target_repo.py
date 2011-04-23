#!/usr/bin/python
""" Quality check participant """

import sys, traceback
from buildservice import BuildService

try:
    import json
except ImportError:
    import simplejson as json

class ParticipantHandler(object):

    """ Participant class as defined by the SkyNET API """

    def __init__(self):
        self.obs = BuildService()

    def handle_wi_control(self, ctrl):
        """ job control thread """
        pass
    
    def handle_lifecycle_control(self, ctrl):
        """ participant control thread """
        pass
    
    def getTargetRepo(self, prj, target_project, target_repository,
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

        result = True
        msg = [] if not wid.lookup("msg") else wid.lookup("msg")
        actions = wid.lookup('actions')
        project = wid.lookup('project')
        repository = wid.lookup('repository')
        archs = wid.lookup('archs')
        archstring = ", ".join(archs)

        # Assert existence and get target repo of interest.
        targetrepo = self.getTargetRepo(actions[0]['sourceproject'],
                                        project, repository, archs)

        if not targetrepo:
            wid.set_field("status","FAILED")
            msg.append("Project %s does not contain a repository that \
                        builds only against project %s repository %s \
                        for architectures %s" % (actions[0]['sourceproject'],
                                                project, repository ,
                                                archstring))
            result = False

        if result :
            wid.set_field("targetrepo", targetrepo)
            msg.append("Target repo %s found." % targetrepo)

        wid.set_field("msg", msg)
        wid.set_result(result)

        return wid


    def handle_wi(self, wid):

        """ actual job thread """

        try:
            # We may want to examine the fields structure
            if 'debug_dump' in wid.fields():
                print json.dumps(wid.to_h(), sort_keys=True, indent=4)

            wid = self.quality_check(wid)

        except Exception as exp :
            print "Failed with exceptions %s " % exp
            wid.set_field("status","FAILED")
            traceback.print_exc(file=sys.stdout)
            wid.set_result(False)
        finally:
            print "Request #%s %s:\n%s" % (wid.lookup('rid'),
                                           wid.lookup('status'),
                                           "\n".join(wid.lookup('msg')))

