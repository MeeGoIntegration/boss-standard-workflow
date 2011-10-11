import os, unittest, sys
from ConfigParser import ConfigParser, NoSectionError, NoOptionError

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

from RuoteAMQP import Workitem, Launcher

TEST_PSTORE = "tests/test_data/process_store"

class TestParticipantHandler(BaseTestParticipantHandler):
    
    module_under_test = "robogrator"

    def launch_override(self, process, fields):
        base = os.path.join(self.process_store, self.project.replace(':', '/'))
        pfile = os.path.join(base, self.evname)
        for psuffix in self.expected.keys():
            pdef = open(pfile + psuffix).read()
            if pdef == process:
                config = self.expected[psuffix]
                # make sure something fails if the same process is launched 2x
                del self.expected[psuffix]
                break # found the right one
        else:
            self.fail("No process found that contains " + repr(process))

        if config is not None:
            for key, value in config.items():
                self.assertTrue(key in fields)
                self.assertEquals(value, fields[key])
        else:
            # old-style process def, or just missing .conf
            self.assertEquals(fields, {"project": self.project})
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
                        os.path.join(os.getcwd(), TEST_PSTORE))
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

        self.process_store = os.path.join(os.getcwd(), TEST_PSTORE)
        pbase = "Chalk:Testing"
        self.evname = "REPO_PUBLISHED"

        self.project = pbase + ":nonexistent"
        self.expected = None
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 0)

        self.project = pbase + ":singleold"
        self.expected = {"": None}
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 1)

        self.project = pbase + ":single"
        self.expected = {".foo.pdef": None}
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 1)

        self.project = pbase + ":single_with_conf"
        self.expected = {".foo.pdef": {'foo':'foo'}}
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 1)

        self.project = pbase + ":single_with_conf_comments"
        self.expected = {".foo.pdef": {'foo':'foo'}}
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 1)

        self.project = pbase + ":single_with_wrong_conf_permissions"
        self.expected = None
        os.chmod(os.path.join(self.process_store,self.project.replace(":","/"))
                + '/' + self.evname + ".foo.conf" , 0)
        self.called_count = 0
        self.assertRaises(RuntimeError, self.participant.launch,
                          self.evname, project=self.project)
        self.assertEquals(self.called_count, 0)
        os.chmod(os.path.join(self.process_store,self.project.replace(":","/"))
                + '/' + self.evname + ".foo.conf" , 0o644)

        self.project = pbase + ":single_with_wrong_permissions"
        self.expected = None
        os.chmod(os.path.join(self.process_store,self.project.replace(":","/"))
                + '/' + self.evname + ".foo.pdef" , 0)
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 0)
        os.chmod(os.path.join(self.process_store,self.project.replace(":","/"))
                + '/' + self.evname + ".foo.pdef" , 0o644)

        self.project = pbase + ":single_with_invalid_conf"
        self.expected = None
        self.called_count = 0
        self.assertRaises(RuntimeError, self.participant.launch,
                          self.evname, project=self.project)
        self.assertEquals(self.called_count, 0)

        self.project = pbase + ":multiple"
        self.expected = {".bar.pdef": None, ".foo.pdef": None}
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 2)

        self.project = pbase + ":multiple_with_conf"
        self.expected = {".bar.pdef": {'bar':'bar'},
                         ".foo.pdef": {'foo': 'foo'}}
        self.called_count = 0
        self.participant.launch(self.evname, project=self.project)
        self.assertEquals(self.called_count, 2)

if __name__ == '__main__':
    unittest.main()
