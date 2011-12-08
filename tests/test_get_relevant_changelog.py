import unittest

from mock import Mock

from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "get_relevant_changelog"
    cl_entry = "* something\n - foo\n - bar\n"

    def setUp(self):
        super(TestParticipantHandler, self).setUp()
        self.entry_queue = [self.cl_entry, self.cl_entry + self.cl_entry]
        self.participant.obs.getCommitLog.return_value = [
                (2, "7a2c826f2733db513c885c7b74f92fa2", "0.2",
                    "2011-09-29 17:44:24", "submitter", "second reviosion"),
                (1, "80ca838decebaffb06f114ad9aa599e4", "0.1",
                    "2011-09-29 17:42:52", "submitter", "first revision")]
        self.participant.obs.getFile.side_efect = self.__get_cl
        self.participant.obs.getPackageFileList.return_value = ["fake.spec"]

    def __get_cl(prj, pkg, rev=None):
        if rev is None:
            return self.entry_queue[-1]
        else:
            return self.entry_queue[rev-1]

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_setup_obs(self):
        self.participant.setup_obs("test_namespace")

    def test_normal(self):
        wid = self.fake_workitem
        wid.fields.ev.actions = self.fake_actions
        self.participant.handle_wi(wid)

    def test_last_revision(self):
        wid = self.fake_workitem
        wid.fields.ev.actions = self.fake_actions
        wid.params.compare = "last_revision"
        self.participant.handle_wi(wid)

    def test_fields_ev_action(self):
        wid = self.fake_workitem
        wid.fields.ev.actions = None
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)

    def test_no_new_entries(self):
        ces = self.mut.get_relevant_changelog(self.cl_entry, self.cl_entry)
        self.assertEqual(len(ces), 0)

    def test_new_entries(self):
        ces = self.mut.get_relevant_changelog(
                "* new entry\n - bar\n\n" + self.cl_entry, self.cl_entry)
        self.assertEqual(len(ces), 1)
        self.assertEqual(ces[0], "* new entry\n - bar\n")

    def test_new_changelog(self):
        ces = self.mut.get_relevant_changelog(self.cl_entry, "")
        self.assertEqual(len(ces), 1)
        self.assertEqual(ces[0], self.cl_entry)

    def test_two_new_changelogs(self):
        ces = self.mut.get_relevant_changelog(self.cl_entry + self.cl_entry, "")
        self.assertEqual(len(ces), 1)
        self.assertEqual(ces[0], self.cl_entry)
if __name__ == '__main__':
    unittest.main()
