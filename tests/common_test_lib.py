"""Fixture common for all test suites in the package."""

import unittest

from mock import Mock
import participants

class BaseTestParticipantHandler(unittest.TestCase):

    def setUp(self):
        mut = __import__(self.__class__.module_under_test)
        mut.BuildService = Mock()
        obs = Mock()
        obs.getFile.return_value = "fake file content"
        obs.getUserEmail.return_value = ""
        obs.getProjectRepositories.return_value = []
        obs.isMaintainer.return_value = False
        obs.getCommitLog.return_value = ""
        obs.getPackageFileList.return_value = ["fake.tar.bz2", "fake.tar.gz",
                                               "fake.tgz", "fake.changes",
                                               "fake.spec", "fake.yaml"]
        mut.BuildService.return_value = obs
        self.participant = mut.ParticipantHandler()
        self.participant.obs = obs
