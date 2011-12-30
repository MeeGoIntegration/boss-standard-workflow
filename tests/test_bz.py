import unittest
from mock import Mock
import ConfigParser
import Cheetah

from bz import prepare_comment
from common_test_lib import BaseTestParticipantHandler

class TestBzFunctions(unittest.TestCase):

    def test_prepare_comment(self):
        text = prepare_comment("testtemplate $key", {"key": "value"})
        self.assertEqual(text, "testtemplate value")

    def test_prepare_comment_utf8(self):
        text = prepare_comment("testtemplate $key", {"key": u"\xe1\xe1"})
        self.assertEqual(text, u"testtemplate \xe1\xe1".encode('utf-8'))

    def test_prepare_comment_notfound(self):
        self.assertRaises(Cheetah.Template.NotFound,
            prepare_comment, "testtemplate $missingkey", {"key": "value"})

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "bz"

    def setUp(self):
        BaseTestParticipantHandler.setUp(self)

        # Mock bugzilla interface without interfering with the real module
        import boss
        self.mockzilla = Mock(spec_set=boss.bz.base.BaseBugzilla)
        self.mut.BugzillaXMLRPC = Mock()
        self.mut.BugzillaXMLRPC.side_effect = self.mockzilla
        self.mut.BugzillaREST = Mock()
        self.mut.BugzillaREST.side_effect = self.mockzilla

        self.config = ConfigParser.SafeConfigParser()
        self.config.read("tests/test_data/bugzilla_right.conf")

        self.bugnum = "1234"
        self.changelog = "* Wed Aug 10 2011 Dmitry Rozhkov <dmitry@example.com> - 0.6.1\n- made changes fixing BMC#%s" % self.bugnum

    def test_setup_config_bad(self):
        self.config.remove_option('meego', 'method')
        self.assertRaises(ConfigParser.NoOptionError,
            self.participant.setup_config, self.config)

    def test_setup_config_bad_filename(self):
        self.config.set('meego', 'comment_template',
                        'tests/test_data/non/existing/filename')
        self.assertRaises(RuntimeError,
            self.participant.setup_config, self.config)

    def test_setup_config_bad_method(self):
        self.config.set('meego', 'method', 'NotRestOrXmlrpc')
        self.assertRaises(RuntimeError,
            self.participant.setup_config, self.config)

    def test_handle_lifecycle_control(self):
        ctrl = Mock()
        ctrl.message = "start"
        ctrl.config = self.config
        self.participant.handle_lifecycle_control(ctrl)

    def test_handle_wi(self):
        self.participant.setup_config(self.config)
        self.fake_workitem.fields.ev.actions = self.fake_actions
        self.participant.handle_wi(self.fake_workitem)

if __name__ == '__main__':
    unittest.main()
