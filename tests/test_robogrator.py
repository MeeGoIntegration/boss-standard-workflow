import os, unittest, sys
from ConfigParser import ConfigParser, NoSectionError, NoOptionError

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

from RuoteAMQP import Workitem, Launcher

class TestParticipantHandler(BaseTestParticipantHandler):
    
    module_under_test = "robogrator"

    def launch_override(self, *args):
        process_store = os.path.join(os.getcwd(), "tests/test_data/process_store")
        base = os.path.join(process_store, self.project.replace(':', '/'))
        pfile = os.path.join(base, self.evname)
        if self.pfile_suffixes[self.called_count]:
            pfile += self.pfile_suffixes[self.called_count]
        self.assertEquals(args[0], open(pfile).read())
        if self.expected_configs[self.called_count]:
            for key, value in self.expected_configs[self.called_count].items():
                self.assertTrue(key in args[1])
                self.assertEquals(value, args[1][key])
        else:
            print args[1]
            self.assertTrue(args[1] == {"project": self.project})
        self.called_count = self.called_count + 1

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
        self.pfile_suffixes = [None]
        self.expected_configs = [None]
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 1)

        self.evname = "REPO_PUBLISHED"
        self.project = "Chalk:Testing:single"
        self.pfile_suffixes = [".foo.pdef"]
        self.expected_configs = [None]
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 1)

        self.evname = "REPO_PUBLISHED"
        self.project = "Chalk:Testing:single_with_conf"
        self.pfile_suffixes = [".foo.pdef"]
        self.expected_configs = [{'foo':'foo'}]
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 1)

        self.evname = "REPO_PUBLISHED"
        self.project = "Chalk:Testing:multiple"
        self.pfile_suffixes = [".bar.pdef", ".foo.pdef"]
        self.expected_configs = [None, None]
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 2)

        self.expected_configs = [{'foo':'foo'}, {'bar':'bar'}]
if __name__ == '__main__':
    unittest.main()
