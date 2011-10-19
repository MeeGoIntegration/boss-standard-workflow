"""Fixture common for all test suites in the package."""

import unittest

from mock import Mock
import participants
import launchers

from RuoteAMQP import Workitem

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
        obs = Mock()
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
