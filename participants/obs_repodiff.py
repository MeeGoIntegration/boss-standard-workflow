#!/usr/bin/python3
"""Generates a diff of 2 obs repositories

:term:`Workitem` params IN:

:Parameters:
    source(string):
        source repository
    target(string):
        target repository

:term:`Workitem` fields OUT

:Parameters:
    repodiff(dict):
        Dictionary will contain fields
          * "src_project" with the source project name
          * "tgt_project" with the target project name
          * "diff" = a dict containing the difference
                  with: 'added'    = list of packages added to the
                                     the target project
                        'modified' = list of packages modified compared
                                     to the target project
                        'removed'  = list of packages removed from
                                     source project compared to the
                                     target project
    msg(list):
       List of string messages, describing the diff, can be used
       for logging

:Returns:
    result(Boolean):
       True if diff was found, false otherwise

"""
from boss.obs import BuildServiceParticipant
import repo_diff

class ParticipantHandler(BuildServiceParticipant):

    def handle_wi_control(self, ctrl):
        pass

    @BuildServiceParticipant.get_oscrc    
    def handle_lifecycle_control(self, ctrl):
        if ctrl.message == "start":
            self.reposerver = ctrl.config.get("obs_repodiff", "reposerver")

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wi):
        if not wi.params.source or not wi.params.target:
            raise RuntimeError("Missing mandatory parameters source and target")
        if not wi.fields.msg:
            wi.fields.msg = []

        for repo in self.obs.getProjectRepositories(wi.params.source):
            if repo in wi.fields.exclude_repos:
                continue
            else:
                src_url = "%s/%s/%s" % ( self.reposerver, wi.params.source.replace(":",":/"), repo)
                break
        for repo in self.obs.getProjectRepositories(wi.params.target):
            if repo in wi.fields.exclude_repos:
                continue
            else:
                trg_url = "%s/%s/%s" % ( self.reposerver, wi.params.target.replace(":",":/"), repo)
                break

        self.log.info("urls: %s and %s" % (src_url, trg_url))

        if wi.params.mode == "short":
            report = repo_diff.generate_short_diff([src_url], [trg_url])
        elif wi.params.mode == "long":
            report = repo_diff.generate_report([src_url], [trg_url])
        else:
            raise RuntimeError("unknown report mode %s" % wi.params.mode)

        wi.result = True
        if report:
            self.log.info(report)
            wi.result = False
            wi.fields.msg.append("Changes in project %s compared to %s, please check." % (wi.params.source, wi.params.target))
            wi.fields.msg.extend(report.split("\n"))

        short_diff = repo_diff.short_diff([src_url], [trg_url])
        if short_diff:
            wi.fields.repodiff = {'src_project':wi.params.source,
                                  'tgt_project':wi.params.target,
                                  'diff':short_diff}

