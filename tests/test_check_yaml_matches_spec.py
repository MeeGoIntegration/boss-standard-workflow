import os, unittest
from ConfigParser import ConfigParser

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

from participants.check_yaml_matches_spec import Lab

from RuoteAMQP import Workitem

WI_TEMPLATE = """
{"fei": { "wfid": "x", "subid": "x", "expid": "x", "engine_id": "x" },
 "fields": {"params": {}, "ev":{}, "debug_dump": true } }
"""

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_yaml_matches_spec"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = ConfigParser()
        self.assertRaises(RuntimeError,
                self.participant.handle_lifecycle_control, ctrl)
        ctrl.config.add_section("obs")
        ctrl.config.set("obs", "oscrc", "oscrc_file")
        self.participant.handle_lifecycle_control(ctrl)
        ctrl.config.add_section("check_yaml")
        ctrl.config.set("check_yaml", "spec_pattern", "test")
        self.participant.handle_lifecycle_control(ctrl)

    def test_setup_obs(self):
        self.participant.setup_obs("test_namespace")

    def test_handle_wi(self):
        import subprocess
        subprocess.Popen = Mock()
        proc = Mock()
        proc.wait.return_value = 0
        subprocess.Popen.return_value = proc

        wid = Workitem(WI_TEMPLATE)
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

        self.participant.spec_re = Mock()
        self.participant.spec_re.search.return_value = True

        fake_action = {
            "type": "submit",
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "sourcerevision": "fake"
        }
        wid.fields.ev.actions = [fake_action, {"type": "test"}]
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

        wid.fields.ev.namespace = "test"

        wid.fields.msg = None

        self.participant.handle_wi(wid)


        wid.fields.ev.actions = []

class TestLab(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.cleanup()

    def test_snapshot_and_cleanup(self):
        snap = self.lab.take_snapshot()
        self.assertEqual(len(self.lab._history), 2)
        for path in self.lab._history:
            self.assertTrue(os.path.exists(path))
        self.lab.get_path("test", snap)
        self.assertRaises(ValueError, self.lab.get_path, "test", 5)

    def test_store(self):
        self.lab.store("test", "testing")
        path = self.lab.get_path("test")
        self.assertTrue(os.path.exists(path))
        self.assertEqual(open(path).read(), "testing")

    def test_get_diff(self):
        self.lab.store("test", "testing")
        self.assertRaises(ValueError, self.lab.get_diff, "test", 5)
        self.assertRaises(ValueError, self.lab.get_diff, "test", 0, 3)
        self.assertEquals(len(self.lab.get_diff("test", 0, 0)), 0)
        snap = self.lab.take_snapshot()
        self.assertEquals(len(self.lab.get_diff("test", snap)), 0)

        open(self.lab.get_path("test"), "w").write("newstuff")
        self.assertEquals(len(self.lab.get_diff("test", snap)), 2)

        self.lab.store("newfile", "newcontent")
        self.assertEquals(len(self.lab.get_diff("newfile", snap)), 1)

        os.remove(self.lab.get_path("test"))
        self.assertEquals(len(self.lab.get_diff("test", snap)), 1)

    def test_context(self):
        class MyException(Exception):
            pass
        try:
            with self.lab:
                raise MyException()
        except MyException:
            self.assertEqual(self.lab.path, None)





if __name__ == '__main__':
    unittest.main()
