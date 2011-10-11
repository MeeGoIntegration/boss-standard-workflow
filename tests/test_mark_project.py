import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "mark_project"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_setup_obs(self):
        self.participant.setup_obs("test_namespace")

    def test_check_and_mark_project(self):
        self.participant.obs.projectAttributeExists.return_value = True
        self.assertFalse(self.participant.check_and_mark_project("project"
                                                                 ,"foo"))
        self.participant.obs.projectAttributeExists.return_value = False
        self.assertTrue(self.participant.check_and_mark_project("project",
                                                                "foo"))

    def test_handle_wi(self):
        wid = Mock()
        wid.fields.ev.project = "Test"
        wid.params.delete = False
        # Test: has attribute -> True
        # This means we don't need to schedule a nightly build
        self.participant.obs.projectAttributeExists.return_value = True
        self.participant.handle_wi(wid)
        self.assertFalse(wid.fields.needs_build)

        # Test: has attribute -> False
        # This means we schedule the nightly build
        self.participant.obs.projectAttributeExists.return_value = False
        self.participant.handle_wi(wid)
        self.assertTrue(wid.fields.needs_build)

        # Test: Project attribute deleted -> True
        # If so, return True
        wid.params.delete = True
        wid.status = False
        self.participant.obs.deleteProjectAttribute.return_value = True
        self.participant.handle_wi(wid)
        self.assertTrue(wid.status)

        # Test: Project attribute deleted -> False
        # If so, return False
        self.participant.obs.deleteProjectAttribute.return_value = False
        self.participant.handle_wi(wid)
        self.assertFalse(wid.status)

if __name__ == '__main__':
    unittest.main()
