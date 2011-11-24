"""Fixture common for all test suites in the package."""

import os, unittest
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

DATADIR = os.environ.get("TESTDATA", None) or \
        os.path.join(os.path.dirname(__file__), "test_data")
FAKE_CONTENT = u"f\xe1ke file content".encode('utf-8')

class BaseTestParticipantHandler(unittest.TestCase):

    def setUp(self):
        self.mut = __import__(self.__class__.module_under_test)
        self.mut.BuildService = Mock()
        obs = Mock(spec_set=BuildService)
        obs.getFile.return_value = FAKE_CONTENT
        obs.getUserEmail.return_value = ""
        obs.getProjectRepositories.return_value = []
        obs.isMaintainer.return_value = False
        obs.getCommitLog.return_value = ""
        obs.getPackageFileList.return_value = ["fake.tar.bz2", "fake.tar.gz",
             "fake.tgz", "fake.changes", "fake.spec", "fake.yaml", u"f\xe1ke"]
        self.mut.BuildService.return_value = obs
        self.participant = self.mut.ParticipantHandler()
        self.participant.obs = obs
        self.fake_workitem = Workitem(WI_TEMPLATE)
        self.fake_actions = [
            {"type": "delete",
             "sourceproject": None, "sourcepackage": None,
             "targetproject": None, "targetpackage": None,
             "deleteproject": "fake_target", "deletepackage": "fake_d"},

            {"type": "change_devel",
             "sourceproject": "fake_source", "sourcepackage": "fake_dv",
             "targetproject": "fake_target", "targetpackage": "fake_dv"},

            {"type": "add_role",
             "sourceproject": None, "sourcepackage": None,
             "targetproject": "fake_target", "targetpackage": None,
             "role": "maintainer", "person": "Admin"},

            {"type": "submit",
             "sourceproject": "fake_source", "sourcepackage": "fake_s",
             "sourcerevision": "1",
             "targetproject": "fake_target", "targetpackage": "fake_t"},

            {"type": "submit",
             "sourceproject": "fake_source", "sourcepackage": "fake_s2",
             "sourcerevision": "5",
             "targetproject": "fake_target", "targetpackage": "fake_t2"}
        ]

    def assertRaises(self, exc_cls, callobj, *args, **kwargs):
        try:
            callobj(*args, **kwargs)
        except exc_cls, exobj:
            return exobj
        else:
            name = getattr(exc_cls, "__name__", str(exc_cls))
            raise self.failureException("%s not raised" % name)


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

    @property
    def target(self):
        result = {}
        for prj, repos in self.repo.iteritems():
            for repo in repos:
                result[prj] = ["%s/%s" % (repo, arch) for arch in
                        self.arch["%s/%s" % (prj, repo)]]
        return result

    def __init__(self, mockobj):
        for name in ["getProjectRepositories", "getRepositoryArchs",
                "getRepositoryTargets", "getTargets"]:
            getattr(mockobj, name).side_effect = getattr(self, name)

    def __fetch(self, source, key):
        try:
            return getattr(self, source, {})[key]
        except KeyError:
            if source == "arch" and key.split('/')[0] in self.repo:
                # This is a hack to make getRepositoryArchs act more like the
                # real thing
                # TODO: Change the repository definition structure and drop this
                # common fetch thingie
                return []
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

    def getTargets(self, project):
        print "getTargets(%s)" % project
        result = self.__fetch("target", project)
        print result
        return result
