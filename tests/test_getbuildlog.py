import os, sys, shutil

assert __name__ != "__main__"
sys.modules["buildservice"] = sys.modules[__name__]

from mock import Mock
from unittest import TestCase
from ConfigParser import ConfigParser
from RuoteAMQP import Workitem

TEMP_DIR = "test_tmp"
WI_TEMPLATE = """
{"fei": { "wfid": "x", "subid": "x", "expid": "x", "engine_id": "x" },
 "fields": {"params": {}, "ev":{}, "debug_dump": true } }
"""

BS_MOCK = Mock()

BuildService = Mock(return_value=BS_MOCK)

import getbuildlog

class ParticipantHandlerTestCase(TestCase):
    """TestCase for getbuildlog participant."""

    def setUp(self):
        """Set up the tests."""
        BS_MOCK.reset_mock()
        BuildService.reset_mock()
        self.participant = getbuildlog.ParticipantHandler()
        os.mkdir(TEMP_DIR)
        config = ConfigParser()
        config.add_section("obs")
        config.set("obs", "oscrc", "oscrc_file")
        config.add_section("getbuildlog")
        config.set("getbuildlog", "logdir", "test_tmp")
        ctrl = Mock()
        ctrl.message = "start"
        ctrl.config = config
        self.participant.handle_lifecycle_control(ctrl)

    def tearDown(self):
        """Tear down the tests."""
        shutil.rmtree(TEMP_DIR)


    def test_handle_wi_control(self):
        """Test participant.handle_wi_control()"""
        ctrl = Mock()
        ctrl.message = "start"
        self.participant.handle_wi_control(ctrl)
        # Does nothing

    def test_handle_lifecycle_control(self):
        """Test participant.handle_lifecycle_control()"""
        participant = getbuildlog.ParticipantHandler()
        config = ConfigParser()
        ctrl = Mock()
        ctrl.message = "start"
        ctrl.config = config

        self.assertRaises(RuntimeError, participant.handle_lifecycle_control,
                ctrl)
        config.add_section("obs")
        config.set("obs", "oscrc", "oscrc_file")
        self.assertRaises(RuntimeError, participant.handle_lifecycle_control,
                ctrl)
        config.add_section("getbuildlog")
        config.set("getbuildlog", "logdir", "test_tmp")

    def test_handle_wi(self):
        """Test participant.handle_wi()"""

        # Test bad values
        wid = Workitem(WI_TEMPLATE)
        wid.fields.__error__ = None
        wid.fields.ev.id = None
        wid.fields.packages = None
        wid.fields.new_failures = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.assertFalse(wid.result)

        # Test failed package
        wid = Workitem(WI_TEMPLATE)
        wid.fields.test_project = "test_project"
        wid.fields.repository = "repo"
        wid.fields.archs = ["i386"]
        wid.fields.new_failures = ["package-a"]
        wid.fields.ev.id = "123"
        wid.fields.msg = None
        BS_MOCK.getPackageResults.return_value = {
                "code": "err",
                "details": "Failed miserably"}
        BS_MOCK.isPackageSucceeded.return_value = False
        BS_MOCK.getBuildLog.return_value = "buildlog"
        self.participant.handle_wi(wid)
        self.assertEqual(len(wid.fields.msg), 1)
        self.assertEqual(len(wid.fields.attachments), 1)
        self.assertTrue(wid.result)

        # Test successful package
        wid = Workitem(WI_TEMPLATE)
        wid.fields.test_project = "test_project"
        wid.fields.repository = "repo"
        wid.fields.archs = ["i386"]
        wid.fields.packages = ["package-a"]
        wid.fields.ev = {}
        wid.fields.ev.id = None
        wid.fields.msg = ["existing message"]
        BS_MOCK.isPackageSucceeded.return_value = True
        self.participant.handle_wi(wid)
        self.assertEqual(len(wid.fields.msg), 2)
        self.assertEqual(len(wid.fields.attachments), 0)
        self.assertTrue(wid.result)
