import os
from mock import Mock
import unittest

from RuoteAMQP.workitem import Workitem

import obs_notify_to


BASE_WORKITEM = '{"fei": 1, "fields": { "params": {}, "ev": {} }}'


class TestParticipantHandler(unittest.TestCase):

    def setUp(self):
        self.participant = notify.ParticipantHandler()
        self.wid = Workitem(BASE_WORKITEM)

        obs = Mock()
        obs_notify_to.BuildService = Mock(return_value=obs)
        obs.getUserData = self.mock_userdata
        obs.getProjectPersons = self.mock_projectpersons

        self.user_data = {'lbt': 'lbt@example.com',
                          'rbraakma': 'rbraakma@example.com',
                          'anberezi': 'anberezi@example.com',
                          'iamer': 'iamer@example.com'}
        self.project_maintainers = {'Project:MINT:Devel':
            ['lbt', 'rbraakma', 'anberezi']}

    def mock_userdata(self, user, *tags):
        self.assertEqual(tags, ['email'])
        return self.user_data[user]

    def mock_projectpersons(self, project, role):
        self.assertEqual(role, 'maintainer')
        return self.project_maintainers[project]

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_empty_params(self):
        self.participant.handle_wi(self.wid)
        self.assertTrue(self.wid.result)
        self.assertFalse(self.wid.fields.mail_to)
        self.assertFalse(self.wid.fields.mail_cc)

    def test_single_user_added_to_users(self):
        self.wid.params.users = ['lbt', 'rbraakma']
        self.wid.params.user = 'iamer'
        self.participant.handle_wi(self.wid)
        self.assertEqual(sorted(self.wid.fields.mail_to),
            ['iamer@example.com', 'lbt@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.wid.fields.mail_cc)

    def test_maintainers(self):
        self.wid.params.maintainers = 'Project:MINT:Devel'
        self.participant.handle_wi(self.wid)
        self.assertEqual(sorted(self.wid.fields.mail_to),
            ['anberezi@example.com', 'lbt@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.wid.fields.mail_cc)

    def test_unknown_user(self):
        self.wid.params.user = 'stranger'
        self.participant.handle_wi(self.wid)
        self.assertTrue("Could not notify unknown user stranger"
                        in self.wid.fields.msg)
        self.assertFalse(self.wid.fields.mail_to)
        self.assertFalse(self.wid.fields.mail_cc)

    def test_unknown_project(self):
        self.wid.params.maintainers = 'Project:Area51'
        self.participant.handle_wi(self.wid)
        self.assertTrue("Could not notify unknown project Project:Area51"
                        in self.wid.fields.msg)
        self.assertFalse(self.wid.fields.mail_to)
        self.assertFalse(self.wid.fields.mail_cc)

    def test_cc(self):
        self.wid.params.users = ['lbt', 'rbraakma']
        self.wid.params.cc = 'True'
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.fields.mail_to)
        self.assertEqual(sorted(self.wid.fields.mail_cc),
            ['lbt@example.com', 'rbraakma@example.com'])

    def test_merge_mail_to(self):
        self.wid.params.users = ['lbt', 'rbraakma']
        self.wid.fields.mail_to = ['user1@example.com']
        self.participant.handle_wi(self.wid)
        self.assertEqual(sorted(self.wid.fields.mail_to,
            ['lbt@example.com', 'rbraakma@example.com', 'user1@example.com'])
        self.assertFalse(self.wid.fields.mail_cc)

    def test_merge_mail_cc(self):
        self.wid.params.users = ['lbt', 'rbraakma']
        self.wid.params.cc = 'True'
        self.wid.fields.mail_cc = ['user1@example.com']
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.fields.mail_to)
        self.assertEqual(sorted(self.wid.fields.mail_cc,
            ['lbt@example.com', 'rbraakma@example.com', 'user1@example.com'])

if __name__ == '__main__':
    unittest.main()
