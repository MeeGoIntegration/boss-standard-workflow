from mock import Mock
import unittest
from common_test_lib import BaseTestParticipantHandler

class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "get_notify_recipients_obs"

    def setUp(self):
        super(TestParticipantHandler, self).setUp()
        self.fake_workitem.fields.ev.namespace = "test"
        self.fake_workitem.fields.ev.who = 'iamer'
        self.fake_workitem.fields.ev.actions = [
            dict(sourcepackage="boss-standard-workflow",
                 sourceproject="home:iamer",
                 sourcerevision="5",
                 targetpackage="boss-standard-workflow",
                 targetproject="Project:MINT:Devel",
                 type="submit"),
        ]

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_empty_params(self):
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.fake_workitem)
        self.assertFalse(self.fake_workitem.result)
        self.assertFalse(self.fake_workitem.fields.mail_to)
        self.assertFalse(self.fake_workitem.fields.mail_cc)

    def test_single_user_added_to_users(self):
        self.fake_workitem.params.users = ['lbt', 'rbraakma']
        self.fake_workitem.params.user = 'iamer'
        self.participant.handle_wi(self.fake_workitem)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_to),
            ['iamer@example.com', 'lbt@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_maintainers_of(self):
        self.fake_workitem.params.maintainers_of = 'Project:MINT:Devel'
        self.participant.handle_wi(self.fake_workitem)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_to),
            ['anberezi@example.com', 'lbt@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_abandoned_project(self):
        self.fake_workitem.params.maintainers_of = 'Project:Abandoned'
        self.participant.handle_wi(self.fake_workitem)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_to), [])
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_role_submitter(self):
        self.fake_workitem.params.role = 'submitter'
        self.participant.handle_wi(self.fake_workitem)
        self.assertEqual(self.fake_workitem.fields.mail_to, ['iamer@example.com'])
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_role_target_project_maintainers(self):
        self.fake_workitem.params.role = 'target project maintainers'
        self.participant.handle_wi(self.fake_workitem)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_to),
            ['anberezi@example.com', 'lbt@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_role_multiple_targets(self):
        # A single SR delivering to multiple projects.
        self.fake_workitem.fields.ev.actions.append(dict(
            sourcepackage="boss-skynet", sourceproject="home:iamer",
            targetpackage="boss-skynet", targetproject="home:pketolai"))
        self.fake_workitem.params.role = 'target project maintainers'
        self.participant.handle_wi(self.fake_workitem)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_to),
            ['anberezi@example.com', 'lbt@example.com',
             'pketolai@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_single_role_added_to_roles(self):
        self.fake_workitem.params.roles = ['submitter']
        self.fake_workitem.params.role = 'target project maintainers'
        self.participant.handle_wi(self.fake_workitem)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_to),
            ['anberezi@example.com', 'iamer@example.com',
             'lbt@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_mixed_parameters(self):
        self.fake_workitem.params.role = 'submitter'
        self.fake_workitem.params.maintainers_of = 'Project:MINT:Devel'
        self.fake_workitem.params.user = 'pketolai'
        self.fake_workitem.params.cc = 'True'
        self.participant.handle_wi(self.fake_workitem)
        self.assertFalse(self.fake_workitem.fields.mail_to)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_cc),
            ['anberezi@example.com', 'iamer@example.com', 'lbt@example.com',
             'pketolai@example.com', 'rbraakma@example.com'])
        self.assertTrue(self.fake_workitem.result)

    def test_unknown_user(self):
        self.fake_workitem.params.user = 'stranger'
        self.participant.handle_wi(self.fake_workitem)
        self.assertTrue("Could not notify stranger (no address found)"
                        in self.fake_workitem.fields.msg)
        self.assertFalse(self.fake_workitem.fields.mail_to)
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_some_users_unknown(self):
        self.fake_workitem.params.users = ['stranger', 'lbt']
        self.participant.handle_wi(self.fake_workitem)
        self.assertTrue("Could not notify stranger (no address found)"
                        in self.fake_workitem.fields.msg)
        self.assertEqual(self.fake_workitem.fields.mail_to, ['lbt@example.com'])
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_unknown_project(self):
        self.fake_workitem.params.maintainers_of = 'Project:Area51'
        self.assertRaises(RuntimeError,
                          self.participant.handle_wi, self.fake_workitem)
        self.assertFalse(self.fake_workitem.fields.mail_to)
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertFalse(self.fake_workitem.result)

    def test_cc(self):
        self.fake_workitem.params.users = ['lbt', 'rbraakma']
        self.fake_workitem.params.cc = 'True'
        self.participant.handle_wi(self.fake_workitem)
        self.assertFalse(self.fake_workitem.fields.mail_to)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_cc),
            ['lbt@example.com', 'rbraakma@example.com'])
        self.assertTrue(self.fake_workitem.result)

    def test_merge_mail_to(self):
        self.fake_workitem.params.users = ['lbt', 'rbraakma']
        self.fake_workitem.fields.mail_to = ['user1@example.com']
        self.participant.handle_wi(self.fake_workitem)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_to),
            ['lbt@example.com', 'rbraakma@example.com', 'user1@example.com'])
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_merge_mail_cc(self):
        self.fake_workitem.params.users = ['lbt', 'rbraakma']
        self.fake_workitem.params.cc = 'True'
        self.fake_workitem.fields.mail_cc = ['user1@example.com']
        self.participant.handle_wi(self.fake_workitem)
        self.assertFalse(self.fake_workitem.fields.mail_to)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_cc),
            ['lbt@example.com', 'rbraakma@example.com', 'user1@example.com'])
        self.assertTrue(self.fake_workitem.result)

    def test_unknown_recipient(self):
        self.fake_workitem.params.recipient = 'Area51'
        self.assertRaises(RuntimeError,
                          self.participant.handle_wi, self.fake_workitem)
        self.assertFalse(self.fake_workitem.fields.mail_to)
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertFalse(self.fake_workitem.result)

    def test_person_recipient(self):
        self.fake_workitem.params.recipient = 'iamer'
        self.participant.handle_wi(self.fake_workitem)
        self.assertEqual(self.fake_workitem.fields.mail_to,
            ['iamer@example.com'])
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_group_recipient(self):
        self.fake_workitem.params.recipient = 'somepeople'
        self.participant.handle_wi(self.fake_workitem)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_to),
            sorted(['lbt@example.com', 'rbraakma@example.com', 'anberezi@example.com', 'pketolai@example.com', 'iamer@example.com']))
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

    def test_project_recipient(self):
        self.fake_workitem.params.recipient = 'Project:MINT:Devel'
        self.participant.handle_wi(self.fake_workitem)
        self.assertEqual(sorted(self.fake_workitem.fields.mail_to),
            sorted(['lbt@example.com', 'rbraakma@example.com', 'anberezi@example.com']))
        self.assertFalse(self.fake_workitem.fields.mail_cc)
        self.assertTrue(self.fake_workitem.result)

if __name__ == '__main__':
    unittest.main()
