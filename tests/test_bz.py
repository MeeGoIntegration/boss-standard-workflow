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
        self.mut.BugzillaXMLRPC = Mock(return_value=self.mockzilla)
        self.mut.BugzillaREST = Mock(return_value=self.mockzilla)

        self.config = ConfigParser.SafeConfigParser()
        self.config.read("tests/test_data/bugzilla_right.conf")
        self.bugnum = "1234"
        self.changelog = "* Wed Aug 10 2011 Dmitry Rozhkov <dmitry@example.com> - 0.6.1\n- made changes fixing BMC#%s" % self.bugnum

        self.bug_status = 'RESOLVED'
        self.bug_resolution = 'FIXED'
        self.expect_status = None
        self.expect_resolution = None
        self.expect_comment = None
        self.bug_get_calls = 0
        self.bug_update_calls = 0

        self.mockzilla.bug_get.side_effect = self.mock_bug_get
        self.mockzilla.bug_update.side_effect = self.mock_bug_update

    def mock_bug_get(self, bugnum):
        self.assertEqual(str(bugnum), str(self.bugnum))
        bug = {'id': str(bugnum), 'token': 'fake_token',
               'status': self.bug_status, 'resolution': self.bug_resolution}
        self.bug_get_calls += 1
        return bug

    def mock_bug_update(self, data):
        self.assertEqual(str(data.get('id')), str(self.bugnum))
        self.assertEqual(data['token'], 'fake_token')
        self.assertEqual(data.get('status'), self.expect_status)
        self.assertEqual(data.get('resolution'), self.expect_resolution)
        if self.expect_comment:
            self.assertEqual(data['comments'][0]['text'], self.expect_comment)
        else:
            self.assertFalse(data.get('comments'))
        self.bug_update_calls += 1

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
        self.assertTrue(self.fake_workitem.result)
        self.assertEqual(self.bug_get_calls, 0)
        self.assertEqual(self.bug_update_calls, 0)

    def test_handle_wi_non_obs(self):
        self.participant.setup_config(self.config)
        self.fake_workitem.fields.ev = None
        self.fake_workitem.fields.package = 'fake_package'
        self.fake_workitem.fields.relevant_changelog = [self.changelog]
        self.participant.handle_wi(self.fake_workitem)
        self.assertTrue(self.fake_workitem.result)
        # two calls, one for meego rest and one for meego xmlrpc
        self.assertEqual(self.bug_get_calls, 2)
        self.assertEqual(self.bug_update_calls, 0)

    def test_handle_action(self):
        self.participant.setup_config(self.config)
        self.fake_workitem.fields.msg = []  # normally handle_wi does this
        self.fake_workitem.result = True
        fake_action = {
            "type": "submit",
            "targetpackage": "fake_package",
            "relevant_changelog": [self.changelog],
        }
        self.expect_comment = "Unit test bugzilla comment\n"
        self.participant.handle_action(fake_action, self.fake_workitem)
        self.assertTrue(self.fake_workitem.result)
        # two calls, one for meego rest and one for meego xmlrpc
        self.assertEqual(self.bug_get_calls, 2)
        self.assertEqual(self.bug_update_calls, 0)

if __name__ == '__main__':
    unittest.main()
