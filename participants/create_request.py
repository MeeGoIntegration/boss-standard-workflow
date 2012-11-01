#!/usr/bin/python
"""Submits a request to OBS with buildservice->createRequest


:term:`Workitem` fields IN

:Parameters:
    hasNewPackages(string):
        if "TRUE", request will be created
    repodiffs(list of dicts):
        for each entry in the list a submit request is created
        with: 'src_project' = source project
              'src_package' = source package
              'tgt_project' = target project
              'tgt_package' = target package
              'diff'        = a dict containing the difference
                  with: 'added'    = list of packages added to the
                                     the target project
                        'modified' = list of packages modified compared
                                     to the target project
                        'removed'  = list of packages removed from
                                     source project compared to the
                                     target project

:term:`Workitem` params IN:

:Parameters:
    comment(string):
        Comment in the state history
    description(string):
        Description for the request, contains normally
        the description why this request was done


:term:`Workitem` fields OUT

:Parameters:
    None

:Returns:
    None
"""
from boss.obs import BuildServiceParticipant
import repo_diff

class ParticipantHandler(BuildServiceParticipant):

    def handle_wi_control(self, ctrl):
        pass

    @BuildServiceParticipant.get_oscrc
    def handle_lifecycle_control(self, ctrl):
        pass

    @BuildServiceParticipant.setup_obs
    def handle_wi(self, wi):
        if not wi.params.comment and not wi.params.description:
            raise RuntimeError("Mandatory parameter 'comment' or 'description' missing")

        if wi.fields.repodiffs:
            for repo in wi.fields.repodiffs:
                my_options_list = []
                for action in repo['diff'].iterkeys():
                    if action == "added" or action == "modified":
                        for pkg in repo['diff'][action]:
                            my_options_list.append({'action': "submit",
                                                    'src_project':repo['src_project'],
                                                    'src_package':pkg,
                                                    'tgt_project':repo['tgt_project'],
                                                    'tgt_package':pkg})
                    elif action == "removed":
                        for pkg in repo['diff'][action]:
                            my_options_list.append({'action': "delete",
                                                    'tgt_project':repo['tgt_project'],
                                                    'tgt_package':pkg})

                self.obs.createRequest(options_list = my_options_list,
                                       description = wi.params.description,
                                       comment = wi.params.comment)

