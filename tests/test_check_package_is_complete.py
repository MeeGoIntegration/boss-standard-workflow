import unittest

from mock import Mock
from RuoteAMQP import Workitem

from common_test_lib import BaseTestParticipantHandler, WI_TEMPLATE

spec_file_content = """Name: test
Version: 0.1
Release:1
Summary: Test
Group: Development/Debuggers
License: GPL2
Source0: test.tar.gz
%description
Test package
"""

dsc_file_content = """Format: 3.0 (quilt)
Source: test
Binary: test
Architecture: all
Version: 0.1-1
Maintainer: Pami Ketolainen <ext-pami.o.ketolainen@nokia.com>
Standards-Version: 3.8.4
Build-Depends: debhelper (>= 7.0.50~)
Checksums-Sha1:
 7d5a63a355ec190c97a874e81161e47892ce1d36 0 test.tar.gz
 7d5a63a355ec190c97a874e81161e47892ce1d36 0 test_0.1-1.debian.tar.gz
Checksums-Sha256:
 02278a94d7481d0763eb91fa5df015b36eb28b3908e45c9fba58c5d2ba15b2ff 0 test.tar.gz
 fbec1b2b2362915969c370d7e3d2ea89319901c9b2f3afd8ca413eeb80c6831c 0 test_0.1-1.debian.tar.gz
Files:
 f9adba90143f6adfd7bfe2a849063547 0 test.tar.gz
 957b14a8710d3247c49cfcaf1ed3b720 0 test_0.1-1.debian.tar.gz
"""

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_package_is_complete"

    def setUp(self):
        super(TestParticipantHandler, self).setUp()
        fake_action = {
                "sourceproject": "fake",
                "sourcepackage": "fake",
                "sourcerevision": "fake",
                "type": "submit"
            }
        self.wid = Workitem(WI_TEMPLATE)
        self.wid.fields.ev.actions = [fake_action]


    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_setup_obs(self):
        self.participant.setup_obs("test_namespace")

    def test_good_package(self):
        self.participant.obs.getPackageFileList.return_value = ["test.spec",
                "test.tar.gz", "test.changes"]
        self.participant.obs.getFile.return_value = spec_file_content
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)

    def test_bad_spec(self):
        self.participant.obs.getPackageFileList.return_value = ["test.spec",
                "test.tar.gz", "test.changes"]
        self.participant.obs.getFile.return_value = "bad spec"
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)

    def test_missing_all(self):
        self.participant.obs.getPackageFileList.return_value = []
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)
        self.assertEqual(self.participant.obs.getFile.call_count, 0)

    def test_bad_sources(self):
        self.participant.obs.getPackageFileList.return_value = ["test.spec",
                "test.changes", "something_else"]
        self.participant.obs.getFile.return_value = spec_file_content
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.result)
        self.assertEqual(self.participant.obs.getFile.call_count, 1)

    def test_missing_actions(self):
        self.wid.fields.ev.actions = []
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)

    def test_get_rpm_sources(self):
        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "type": "submit"
        }
        self.assertRaises(self.mut.SourceError,
                self.participant.get_rpm_sources, fake_action, [])

        self.participant.obs.getFile.return_value = "bad spec"
        self.assertRaises(self.mut.SourceError,
                self.participant.get_rpm_sources, fake_action, ["test.spec"])

        self.participant.obs.getFile.return_value = spec_file_content
        sources = self.participant.get_rpm_sources(fake_action, ["test.spec"])
        self.assertEqual(self.participant.obs.getFile.call_args[0],
                ("fake", "fake", "test.spec", "fake"))
        self.assertEqual(sources, ["test.tar.gz"])

    def test_get_deb_sources(self):
        fake_action = {
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake",
            "type": "submit"
        }
        self.assertRaises(self.mut.SourceError,
                self.participant.get_deb_sources, fake_action, [])

        self.participant.obs.getFile.return_value = "bad dsc"
        self.assertRaises(self.mut.SourceError,
                self.participant.get_deb_sources, fake_action, ["test.dsc"])

        self.participant.obs.getFile.return_value = dsc_file_content
        sources = self.participant.get_deb_sources(fake_action, ["test.dsc"])
        self.assertEqual(self.participant.obs.getFile.call_args[0],
                ("fake", "fake", "test.dsc", "fake"))
        self.assertEqual(sources, ["test.tar.gz", "test_0.1-1.debian.tar.gz"])

if __name__ == '__main__':
    unittest.main()
