import os, sys, shutil

from mock import Mock
from unittest import TestCase
from ConfigParser import ConfigParser
from RuoteAMQP import Workitem
from common_test_lib import WI_TEMPLATE, BaseTestParticipantHandler

TEMP_DIR = "test_tmp"

class ParticipantHandlerTestCase(BaseTestParticipantHandler):
    """TestCase for getbuildlog participant."""

    module_under_test = "getbuildlog"

    def setUp(self):
        """Set up the tests."""
        BaseTestParticipantHandler.setUp(self)
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
        BaseTestParticipantHandler.tearDown(self)
        shutil.rmtree(TEMP_DIR)

    def test_handle_wi_control(self):
        """Test participant.handle_wi_control()"""
        ctrl = Mock()
        ctrl.message = "start"
        self.participant.handle_wi_control(ctrl)
        # Does nothing

    def test_handle_lifecycle_control(self):
        """Test participant.handle_lifecycle_control()"""
        config = ConfigParser()
        ctrl = Mock()
        ctrl.message = "start"
        ctrl.config = config

        self.assertRaises(RuntimeError,
                self.participant.handle_lifecycle_control, ctrl)
        config.add_section("obs")
        config.set("obs", "oscrc", "oscrc_file")
        self.assertRaises(RuntimeError,
                self.participant.handle_lifecycle_control, ctrl)
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
        self.participant.obs.getPackageResults.return_value = {
                "code": "err",
                "details": "Failed miserably"}
        self.participant.obs.isPackageSucceeded.return_value = False
        self.participant.obs.getBuildLog.return_value = "buildlog"
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
        self.participant.obs.isPackageSucceeded.return_value = True
        self.participant.handle_wi(wid)
        self.assertEqual(len(wid.fields.msg), 2)
        self.assertEqual(len(wid.fields.attachments), 0)
        self.assertTrue(wid.result)
