import os, shutil
from mock import Mock
from subprocess import check_call, PIPE
from urllib.error import HTTPError
from io import StringIO

from common_test_lib import BaseTestParticipantHandler, DATADIR

RPM_NAME = "test-configurations-0.1-1.noarch.rpm"

def download_mock(project, target, package, binary, path):
    try:
        shutil.copy(os.path.join(DATADIR, binary),
            path)
    except IOError:
        raise HTTPError("http://%s/%s/%s/%s" %
                (project, package, target, binary),
                404, "Not found", [], StringIO("File not found"))

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "get_kickstarts"

    @classmethod
    def setUpClass(cls):
        check_call(['make','confsrpm'], cwd=DATADIR, stdout=PIPE, stderr=PIPE)

    @classmethod
    def tearDownClass(cls):
        check_call(['make','clean'], cwd=DATADIR, stdout=PIPE, stderr=PIPE)

    def setUp(self):
        super(TestParticipantHandler, self).setUp()
        self.fake_workitem.fields.image_configurations = {
                "test-configurations":{
                    "test_repo/i586": [RPM_NAME]}}
        self.fake_workitem.fields.ev.namespace = "test"
        self.fake_workitem.params.project = "project"
        self.participant.obs.getBinary.side_effect = download_mock

    def test_lifecycle_control(self):
        self.participant.handle_lifecycle_control(Mock())

    def test_wi_control(self):
        self.participant.handle_wi_control(Mock())

    def test_params(self):
        wid = self.fake_workitem.dup()
        wid.fields.image_configurations = None
        exc = self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.assertTrue("image_configurations" in str(exc))
        wid.fields.image_configurations = ["this should be dict"]
        exc = self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.assertTrue("dictionary" in str(exc))
        wid.fields.image_configurations = \
                self.fake_workitem.fields.image_configurations

        wid.params.project = None
        exc = self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.assertTrue("project" in str(exc))
        wid.params.project = self.fake_workitem.params.project

        wid.fields.ignore_ks = "not a list"
        exc = self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.assertTrue("ignore_ks" in str(exc))

    def test_normal(self):
        self.participant.handle_wi(self.fake_workitem)
        self.assertTrue(self.fake_workitem.result)
        kickstarts = self.fake_workitem.fields.kickstarts
        self.assertEqual(len(kickstarts), 1)
        self.assertEqual(kickstarts[0]["basename"], "test-image.ks")
        self.assertEqual(kickstarts[0]["basedir"], "./usr/share/configurations")
        self.assertEqual(kickstarts[0]["contents"], "# Dummy file\n")

    def test_download_fail(self):
        wid = self.fake_workitem
        confs = wid.fields.image_configurations.as_dict()
        confs["some-other-package"] = {
                    "test_repo/i586": ["doesnotexist.rpm"]}
        wid.fields.image_configurations = confs
        exc = self.assertRaises(Exception, self.participant.handle_wi, wid)
        self.assertTrue("some-other-package" in str(exc))
        self.assertTrue("test_repo/i586" in str(exc))
        self.assertTrue("doesnotexist.rpm" in str(exc))

    def test_no_ks_in_package(self):
        real_er = self.mut.extract_rpm
        self.mut.extract_rpm = Mock()
        self.mut.extract_rpm.return_value = []
        wid = self.fake_workitem
        try:
            self.participant.handle_wi(wid)
            self.assertFalse(wid.result)
            self.assertEqual(len(wid.fields.msg), 1)
            self.assertTrue("did not contain .ks" in wid.fields.msg[0])
        finally:
            self.mut.extract_rpm = real_er

    def test_ignore_ks(self):
        wid = self.fake_workitem
        wid.fields.ignore_ks = ["test-image.ks"]
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)
        self.assertEqual(len(wid.fields.kickstarts), 0)


if __name__ == "__main__":
    # Plain unittest.main() does not run class setup/teardown
    #unittest.main()
    print("!!Not supported!!! run with nosetests")
