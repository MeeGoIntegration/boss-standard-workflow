"""Unit tests for defineimage participant."""

import sys

from ConfigParser import ConfigParser
from mock import Mock
from unittest import TestCase

from RuoteAMQP.workitem import Workitem

from common_test_lib import BaseTestParticipantHandler
import defineimage

class HelpersTestCase(TestCase):
    """Test case for defineimage participant helper functions."""

    def test_select_subpkgs(self):
        """Test select_subpkgs()."""
        # test empy list
        pkglist = []
        selected = defineimage.select_subpkgs(pkglist, "foo")
        self.assertEqual(len(selected), 0)
        # test ignored packages
        pkglist = ["foo-debuginfo", "foo-devel", "foo-doc", "bar"]
        selected = defineimage.select_subpkgs(pkglist, "foo")
        self.assertEqual(len(selected), 1)
        # test valid packages
        pkglist = ["foo-tests", "foo-unit-tests"]
        selected = defineimage.select_subpkgs(pkglist, "foo")
        self.assertEqual(len(selected), 2)
        pkglist = ["foo-tests"]
        selected = defineimage.select_subpkgs(pkglist, "foo-tests")
        self.assertEqual(len(selected), 1)


class ParticipantHandlerTestCase(BaseTestParticipantHandler):
    """Test case for defineimage participant."""

    module_under_test = "defineimage"

    def setUp(self): # pylint: disable=C0103
        """Test setup."""
        BaseTestParticipantHandler.setUp(self)
        ctrl = Mock()
        ctrl.message = "start"
        ctrl.config = ConfigParser()
        ctrl.config.add_section("obs")
        ctrl.config.add_section("defineimage")
        ctrl.config.add_section("testing")
        ctrl.config.set("obs", "oscrc", "oscrc_file")
        ctrl.config.set("defineimage", "imagetypes", "testing")
        ctrl.config.set("testing", "always_include", "base-tests")
        self.ctrl = ctrl

    def test_handle_wi_control(self):
        """Test handle_wi_control()."""
        self.participant.handle_wi_control(Mock())
        # Does nothing atm

    def test_setup_obs(self):
        """Test setup_obs()."""
        self.participant.handle_lifecycle_control(self.ctrl)
        self.participant.setup_obs("my_namespace")
        self.mut.BuildService.assert_called_with(oscrc="oscrc_file",
                apiurl="my_namespace")

    def test_handle_lifecycle_control(self):
        """Test handle_lifecycle_control()."""
        self.participant.handle_lifecycle_control(self.ctrl)
        self.assertEqual(self.participant.oscrc, "oscrc_file")
        self.assertTrue("testing" in self.participant.image_options)

    def test_handle_wi(self):
        """Test handle_wi()."""
        # Pylint does not handle Workitem content
        # pylint: disable=E1101
        self.participant.handle_lifecycle_control(self.ctrl)
        wid = self.fake_workitem
        wid.fields.ev.namespace = "test"
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.assertFalse(wid.result)

        wid.params.image_type = "bad_image"
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

        wid.params.image_type = "testing"
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

        wid.fields.test_project = "test_project"
        wid.fields.repository = "repository"
        wid.fields.image = {}
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

        wid.fields.image.arch = "i386"
        wid.fields.image.packages = ["foo"]
        self.participant.obs.getPackageReverseDepends.return_value = ["bar"]
        self.participant.obs.getPackageSubpkgs.return_value = ["foo-tests", "foo-devel"]
        self.participant.handle_wi(wid)
        self.assertEqual(len(wid.fields.image.packages), 4)
        self.assertTrue("foo" in wid.fields.image.packages)
        self.assertTrue("foo-tests" in wid.fields.image.packages)
        self.assertTrue("foo-devel" not in wid.fields.image.packages)
        self.assertTrue("bar" in wid.fields.image.packages)
        self.assertTrue("base-tests" in wid.fields.image.packages)
