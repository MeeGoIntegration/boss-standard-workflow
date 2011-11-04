import os, shutil, unittest
from mock import Mock
from subprocess import check_call, PIPE
from common_test_lib import BaseTestParticipantHandler, BuildServiceFakeRepos, \
        DATADIR

def download_mock(project, target, package, binary, path):
    shutil.copy(os.path.join(DATADIR, "test-configurations-0.1-1.noarch.rpm"),
            path)

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "download_kickstarts"

    @classmethod
    def setUpClass(cls):
        check_call(['make','confsrpm'], cwd=DATADIR, stdout=PIPE, stderr=PIPE)

    @classmethod
    def tearDownClass(cls):
        check_call(['make','clean'], cwd=DATADIR, stdout=PIPE, stderr=PIPE)

    def setUp(self):
        super(TestParticipantHandler, self).setUp()
        self.fake_workitem.fields.ev.namespace = "test"
        self.repos = BuildServiceFakeRepos(self.participant.obs)
        self.participant.obs.getBinaryList.return_value = []
        self.participant.obs.getBinary.side_effect=download_mock

        self.repos.repo["otherproject"] = ["repo"]
        self.repos.arch["otherproject/repo"] = ["i586"]
        self.repos.path["otherproject/repo"] = ["target/repo"]

    def tearDown(self):
        super(TestParticipantHandler, self).tearDown()

    def test_lifecycle_control(self):
        self.participant.handle_lifecycle_control(Mock())

    def test_wi_control(self):
        self.participant.handle_wi_control(Mock())

    def test_params(self):
        wid = self.fake_workitem
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        wid.params.conf_package = "test-configurations"
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        wid.fields.project = "project"
        wid.fields.ignore_ks = "something"
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        wid.fields.ignore_ks = None
        self.participant.handle_wi(wid)

    def test_ks_extract(self):
        wid = self.fake_workitem
        wid.params.conf_package = "test-configurations"
        wid.fields.project = "project"
        self.participant.obs.getBinaryList.return_value = [
                "test-configurations-0.1-1.noarch.rpm", "something else"]
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)
        self.participant.obs.getBinaryList.assert_called_with(
                "project", "repo/i586", "test-configurations")
        self.assertEqual(len(wid.fields.images), 1)
        self.assertEqual(wid.fields.images[0]["name"], "test-image")
        self.assertEqual(wid.fields.images[0]["kickstart"], "# Dummy file\n")

    def test_ignore_ks(self):
        wid = self.fake_workitem
        wid.params.conf_package = "test-configurations"
        wid.fields.project = "project"
        wid.fields.ignore_ks = ["test-image.ks"]
        self.participant.obs.getBinaryList.return_value = [
                "test-configurations-0.1-1.noarch.rpm"]
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)
        self.assertEqual(len(wid.fields.images), 0)

    def test_sr_package(self):
        wid = self.fake_workitem
        fake_action = {"sourcepackage": "test-configurations",
                "sourceproject": "otherproject"}
        wid.fields.ev.actions = [fake_action]

        wid.params.conf_package = "test-configurations"
        wid.fields.project = "project"
        self.participant.obs.getBinaryList.return_value = []

        self.participant.handle_wi(wid)
        # No binaries found
        self.assertEqual(len(wid.fields.images), 0)
        self.participant.obs.getBinaryList.assert_called_with(
                "otherproject", "repo/i586", "test-configurations")

if __name__ == "__main__":
    # Plain unittest.main() does not run class setup/teardown
    #unittest.main()
    print "!!Not supported!!! run with nosetests"
