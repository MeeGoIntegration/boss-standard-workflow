import unittest
from mock import Mock
from ConfigParser import SafeConfigParser

from bz import bz_opener, get_bug, put_bug, bz_state_comment, \
        get_bug_attr, prepare_comment, handle_mentioned_bug, \
        ParticipantHandler

class TestBzFunctions(unittest.TestCase):

    def setUp(self):
        import urllib2
        import bz
        fake_data = Mock()
        fake_data.read = Mock()
        fake_data.read.return_value = """
            {
                "test_attr": "test_value",
                "update_token": "bla bla",
                "status": "NEW",
                "resolution": "RESOLVED"
            }
        """
        fake_opener = Mock()
        fake_opener.open.return_value = fake_data
        bz.urllib2 = Mock(urllib2)
        bz.urllib2.build_opener = Mock()
        bz.urllib2.build_opener.return_value = fake_opener

        self.bugzilla = {
            "method": "GET",
            "bugzilla_server": "http://bserver/",
            "rest_slug": "slug",
            "bugzilla_user": "user",
            "bugzilla_pwd": "pwd",
            "cookies": {
                "Bugzilla_login": "blogin",
                "Bugzilla_logincookie": "bcookie"
            }
        }

    def test_bz_opener(self):
        bz_opener(self.bugzilla, "some_url")
        bz_opener(self.bugzilla, "some_url", method="GET",
                  data={"test_key": "test_value"})

    def test_get_bug(self):
        get_bug(self.bugzilla, 12345)

    def test_put_bug(self):
        put_bug(self.bugzilla, 12345, {"test_key": "test_value"})

    def test_get_bug_attr(self):
        self.assertEqual(None, get_bug_attr(self.bugzilla, 12345,
                                            "non-existing"))
        self.bugzilla["method"] = "REST"
        self.assertEqual(None, get_bug_attr(self.bugzilla, 12345,
                                            "non-existing"))
        self.assertEqual("test_value",
                         get_bug_attr(self.bugzilla, 12345, "test_attr"))

    def test_prepare_comment(self):
        prepare_comment("testtemplate $key", {"key": "value"})

    def test_bz_state_comment(self):
        self.assertFalse(
                   bz_state_comment(self.bugzilla, 12345, "NEW", "", wi=None))
        self.bugzilla["method"] = "REST"
        self.assertTrue(bz_state_comment(self.bugzilla, 12345, "NEW",
                                         "FAKE_RES", wi=Mock()))

    def test_handle_mentioned_bug(self):
        result = {"fbugnums": []}
        handle_mentioned_bug(self.bugzilla, 12345, Mock(), result)
        # OMG!!! result value has changed (not pythonic)
        self.assertEqual({"fbugnums": [12345]}, result)

class TestParticipantHandler(unittest.TestCase):

    def setUp(self):
        self.participant = ParticipantHandler()

        # Mock bugzilla server
        import urllib2
        import bz
        fake_info = Mock()
        fake_info.getallmatchingheaders.return_value = ["Headers:key=value;"]
        fake_resp = Mock()
        fake_resp.info.return_value = fake_info
        bz.urllib2 = Mock(urllib2)
        fake_opener = Mock()
        fake_opener.open.return_value = fake_resp
        bz.urllib2.build_opener = Mock()
        bz.urllib2.build_opener.return_value = fake_opener

        self.config = SafeConfigParser()
        self.config.read("tests/test_data/bugzilla_right.conf")

    def test_setup_config(self):
        config = SafeConfigParser()
        config.read("tests/test_data/bugzilla_wrong.conf")
        self.assertRaises(Exception, self.participant.setup_config, config)
        self.participant.setup_config(self.config)

    def test_get_cookie(self):

        config = SafeConfigParser()
        config.read("tests/test_data/bugzilla_right.conf")
        self.participant.setup_config(config)
        self.participant.get_cookies()

    def test_handle_lifecycle_control(self):
        ctrl = Mock()
        ctrl.message = "start"
        ctrl.config = self.config
        self.participant.handle_lifecycle_control(ctrl)

    def test_handle_wi(self):
        workitem = Mock()
        workitem.params = Mock()
        workitem.params.test = False
        workitem.fields = Mock()
        workitem.fields.ev = Mock()
        workitem.fields.ev.actions = []
        self.participant.bzs = {}
        self.participant.handle_wi(workitem)

if __name__ == '__main__':
    unittest.main()
