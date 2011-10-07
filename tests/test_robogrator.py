import os, unittest, sys
from ConfigParser import ConfigParser, NoSectionError, NoOptionError

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

from RuoteAMQP import Workitem, Launcher

class TestParticipantHandler(BaseTestParticipantHandler):
    
    module_under_test = "robogrator"

    def launch_override(self, *args, **kwargs):
        process_store = os.path.join(os.getcwd(), "tests/test_data/process_store")
        base = os.path.join(process_store, self.project.replace(':', '/'))
        pfile = os.path.join(base, self.evname)
        if self.pfile_suffix:
            pfile += self.pfile_suffix
        self.assertEquals(args[0], open(pfile).read())
        if self.expected_config:
            for key, value in self.expected_config.items():
                self.assertIn(key, kwargs)
                self.assertEquals(value, kwargs[key])

    def setup_ctrl(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = ConfigParser()
        ctrl.config.add_section("robogrator")
        ctrl.config.add_section("boss")
        ctrl.config.add_section("irc")
        ctrl.config.set("boss", "amqp_host", "127.0.0.1")
        ctrl.config.set("boss", "amqp_user", "boss")
        ctrl.config.set("boss", "amqp_pwd", "boss")
        ctrl.config.set("boss", "amqp_vhost", "boss")
        ctrl.config.set("robogrator", "process_store",
                        os.path.join(os.getcwd(),
                                     "tests/test_data/process_store"))
        self.ctrl = ctrl

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = ConfigParser()
        self.assertRaises(NoSectionError,
                self.participant.handle_lifecycle_control, ctrl)
        ctrl.config.add_section("robogrator")
        self.assertRaises(NoOptionError,
                self.participant.handle_lifecycle_control, ctrl)

        self.setup_ctrl()
        self.assertRaises(IOError, self.participant.handle_lifecycle_control,
                ctrl)
        self.mut.Launcher = Mock()
        self.participant.handle_lifecycle_control(ctrl)
        assert hasattr(self.participant, "launcher")

    def test_launch(self):
        self.mut.Launcher = Mock()
        self.setup_ctrl()
        self.participant.handle_lifecycle_control(self.ctrl)
        self.participant.launcher.launch = self.launch_override
        self.evname = "REPO_PUBLISHED"
        self.project = "Chalk:Testing:singleold"
        self.pfile_suffix = None
        self.expected_config = None
        self.participant.launch(self.evname, project=self.project)
        self.evname = "REPO_PUBLISHED"
        self.project = "Chalk:Testing:single"
        self.pfile_suffix = ".foo.pdef"
        self.expected_config = None
        self.participant.launch(self.evname, project=self.project)
        self.evname = "REPO_PUBLISHED"
        self.project = "Chalk:Testing:single_with_conf"
        self.pfile_suffix = ".foo.pdef"
        self.expected_config = {'foo':'foo'}
        self.participant.launch(self.evname, project=self.project)

if __name__ == '__main__':
    unittest.main()
