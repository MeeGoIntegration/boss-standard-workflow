import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "check_package_built_at_source"

    def setUp(self):
        super(TestParticipantHandler, self).setUp()
        fake_action = {
            "type" : "submit",
            "sourceproject": "fake",
            "sourcepackage": "fake",
            "targetproject": "fake"
        }
        self.fake_workitem.fields.ev.actions = [fake_action]
        self.fake_workitem.fields.ev.namespace = "test"

        self.participant.obs.getProjectRepositories.return_value = ["test_repo"]
        self.participant.obs.getRepositoryArchs.return_value = ["i586"]

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_success(self):
        wid = self.fake_workitem
        self.participant.obs.getPackageStatus.return_value = {
                "test_repo/i586":"succeeded"}
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)
        self.assertEqual(len(wid.fields.msg), 0)

    def test_failure(self):
        wid = self.fake_workitem
        self.participant.obs.getPackageStatus.return_value = {
                "test_repo/i586":"failed"}
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)
        self.assertEqual(len(wid.fields.msg), 1)

    def test_other_status(self):
        wid = self.fake_workitem
        self.participant.obs.getPackageStatus.return_value = {
                "test_repo/i586": "somethingelse"}
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)
        self.assertEqual(len(wid.fields.msg), 1)

    def test_params(self):
        wid = self.fake_workitem
        wid.fields.msg = None
        self.fake_workitem.fields.ev.namespace = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.fake_workitem.fields.ev.namespace = "test"
        wid.fields.ev.actions = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)



if __name__ == '__main__':
    unittest.main()
