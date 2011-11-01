"""Fixture common for all test suites in the package."""

import unittest
from urllib2 import HTTPError
from mock import Mock
import participants
import launchers

from RuoteAMQP import Workitem
from buildservice import BuildService

# JSON template for initializing Workitem
WI_TEMPLATE = """
{"fei": { "wfid": "x", "subid": "x", "expid": "x", "engine_id": "x" },
 "fields": {"params": {}, "ev":{}, "debug_dump": true },
 "participant_name" : "fake_participant" }
"""

class BaseTestParticipantHandler(unittest.TestCase):

    def setUp(self):
        self.mut = __import__(self.__class__.module_under_test)
        self.mut.BuildService = Mock()
        obs = Mock(spec_set=BuildService)
        obs.getFile.return_value = "fake file content"
        obs.getUserEmail.return_value = ""
        obs.getProjectRepositories.return_value = []
        obs.isMaintainer.return_value = False
        obs.getCommitLog.return_value = ""
        obs.getPackageFileList.return_value = ["fake.tar.bz2", "fake.tar.gz",
                                               "fake.tgz", "fake.changes",
                                               "fake.spec", "fake.yaml"]
        self.mut.BuildService.return_value = obs
        self.participant = self.mut.ParticipantHandler()
        self.participant.obs = obs
        self.fake_workitem = Workitem(WI_TEMPLATE)


class BuildServiceFakeRepos(object):

    repo = {
            "project": ["repo"],
            }
    arch = {
            "project/repo":["i586"],
            }
    path = {
            "project/repo":["target/repo"],
            }

    def __init__(self, mockobj):
        for name in ["getProjectRepositories", "getRepositoryArchs",
                "getRepositoryTargets"]:
            getattr(mockobj, name).side_effect = getattr(self, name)

    def __fetch(self, source, key):
        try:
            return getattr(self, source, {})[key]
        except KeyError:
            raise HTTPError("%s:%s" % (source, key), 404, "", {}, None)

    def getProjectRepositories(self, project):
        print "getProjectRepositories(%s)" % project
        return self.__fetch("repo", project)

    def getRepositoryArchs(self, project, repository):
        print "getRepositoryArchs(%s, %s)" % (project, repository)
        return self.__fetch("arch", "%s/%s" % (project, repository))

    def getRepositoryTargets(self, project, repository):
        print "getRepositoryTargets(%s, %s)" % (project, repository)
        return self.__fetch("path", "%s/%s" % (project, repository))
