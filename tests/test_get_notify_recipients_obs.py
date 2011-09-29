from ConfigParser import SafeConfigParser
import os
from mock import Mock
import unittest
import urllib2

from RuoteAMQP.workitem import Workitem
from SkyNET.Control import WorkItemCtrl

import get_notify_recipients_obs as mut


BASE_WORKITEM = '{"fei": 1, "fields": { "params": {}, "ev": {} }}'


class TestParticipantHandler(unittest.TestCase):

    def setUp(self):
        self.participant = mut.ParticipantHandler()
        self.wid = Workitem(BASE_WORKITEM)
        self.wid.fields.ev.namespace = 'mock_apiurl'
        self.wid.fields.ev.who = 'iamer'
        self.wid.fields.ev.actions = [
            dict(sourcepackage="boss-standard-workflow",
                 sourceproject="home:iamer",
                 sourcerevision="5",
                 targetpackage="boss-standard-workflow",
                 targetproject="Project:MINT:Devel",
                 type="submit"),
        ]

        # Guard against interface changes in BuildService
        self.assertTrue(hasattr(mut.BuildService, 'getUserData'))
        self.assertTrue(hasattr(mut.BuildService, 'getProjectPersons'))
        obs = Mock()
        mut.BuildService = Mock(return_value=obs)
        obs.getUserData = self.mock_userdata
        obs.getProjectPersons = self.mock_projectpersons

        self.user_data = {'lbt': 'lbt@example.com',
                          'rbraakma': 'rbraakma@example.com',
                          'anberezi': 'anberezi@example.com',
                          'iamer': 'iamer@example.com',
                          'pketolai': 'pketolai@example.com'}
        self.project_maintainers = {
            'Project:MINT:Devel': ['lbt', 'rbraakma', 'anberezi'],
            'home:pketolai': ['pketolai'],
            'Project:Abandoned': []
        }

    def mock_userdata(self, user, *tags):
        self.assertEqual(tags, ('email',))
        try:
            return [self.user_data[user]]
        except KeyError:
            return []

    def mock_projectpersons(self, project, role):
        self.assertEqual(role, 'maintainer')
        try:
            return self.project_maintainers[project]
        except KeyError:
            # mimic what buildservice does on error
            error = "%s Not Found" % project
            raise urllib2.HTTPError("url", 404, error, None, None)

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = WorkItemCtrl('start')
        ctrl.config = SafeConfigParser()
        ctrl.config.add_section("obs")
        ctrl.config.set("obs", "oscrc", "mock oscrc")
        self.participant.handle_lifecycle_control(ctrl)

    def test_handle_lifecycle_control_error(self):
        ctrl = WorkItemCtrl('start')
        ctrl.config = SafeConfigParser()
        self.assertRaises(RuntimeError,
                          self.participant.handle_lifecycle_control, ctrl)

    def test_empty_params(self):
        self.assertRaises(RuntimeError, self.participant.handle_wi, self.wid)
        self.assertFalse(self.wid.result)
        self.assertFalse(self.wid.fields.mail_to)
        self.assertFalse(self.wid.fields.mail_cc)

    def test_single_user_added_to_users(self):
        self.wid.params.users = ['lbt', 'rbraakma']
        self.wid.params.user = 'iamer'
        self.participant.handle_wi(self.wid)
        self.assertEqual(sorted(self.wid.fields.mail_to),
            ['iamer@example.com', 'lbt@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.wid.fields.mail_cc)
        self.assertTrue(self.wid.result)

    def test_maintainers_of(self):
        self.wid.params.maintainers_of = 'Project:MINT:Devel'
        self.participant.handle_wi(self.wid)
        self.assertEqual(sorted(self.wid.fields.mail_to),
            ['anberezi@example.com', 'lbt@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.wid.fields.mail_cc)
        self.assertTrue(self.wid.result)

    def test_abandoned_project(self):
        self.wid.params.maintainers_of = 'Project:Abandoned'
        self.participant.handle_wi(self.wid)
        self.assertEqual(sorted(self.wid.fields.mail_to), [])
        self.assertFalse(self.wid.fields.mail_cc)
        self.assertTrue(self.wid.result)

    def test_role_submitter(self):
        self.wid.params.role = 'submitter'
        self.participant.handle_wi(self.wid)
        self.assertEqual(self.wid.fields.mail_to, ['iamer@example.com'])
        self.assertFalse(self.wid.fields.mail_cc)
        self.assertTrue(self.wid.result)

    def test_role_target_project_maintainers(self):
        self.wid.params.role = 'target project maintainers'
        self.participant.handle_wi(self.wid)
        self.assertEqual(sorted(self.wid.fields.mail_to),
            ['anberezi@example.com', 'lbt@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.wid.fields.mail_cc)
        self.assertTrue(self.wid.result)

    def test_role_multiple_targets(self):
        # A single SR delivering to multiple projects.
        self.wid.fields.ev.actions.append(dict(
            sourcepackage="boss-skynet", sourceproject="home:iamer",
            targetpackage="boss-skynet", targetproject="home:pketolai"))
        self.wid.params.role = 'target project maintainers'
        self.participant.handle_wi(self.wid)
        self.assertEqual(sorted(self.wid.fields.mail_to),
            ['anberezi@example.com', 'lbt@example.com',
             'pketolai@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.wid.fields.mail_cc)
        self.assertTrue(self.wid.result)

    def test_single_role_added_to_roles(self):
        self.wid.params.roles = ['submitter']
        self.wid.params.role = 'target project maintainers'
        self.participant.handle_wi(self.wid)
        self.assertEqual(sorted(self.wid.fields.mail_to),
            ['anberezi@example.com', 'iamer@example.com',
             'lbt@example.com', 'rbraakma@example.com'])
        self.assertFalse(self.wid.fields.mail_cc)
        self.assertTrue(self.wid.result)

    def test_mixed_parameters(self):
        self.wid.params.role = 'submitter'
        self.wid.params.maintainers_of = 'Project:MINT:Devel'
        self.wid.params.user = 'pketolai'
        self.wid.params.cc = 'True'
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.fields.mail_to)
        self.assertEqual(sorted(self.wid.fields.mail_cc),
            ['anberezi@example.com', 'iamer@example.com', 'lbt@example.com',
             'pketolai@example.com', 'rbraakma@example.com'])
        self.assertTrue(self.wid.result)

    def test_unknown_user(self):
        self.wid.params.user = 'stranger'
        self.participant.handle_wi(self.wid)
        self.assertTrue("Could not notify stranger (no address found)"
                        in self.wid.fields.msg)
        self.assertFalse(self.wid.fields.mail_to)
        self.assertFalse(self.wid.fields.mail_cc)
        self.assertTrue(self.wid.result)

    def test_some_users_unknown(self):
        self.wid.params.users = ['stranger', 'lbt']
        self.participant.handle_wi(self.wid)
        self.assertTrue("Could not notify stranger (no address found)"
                        in self.wid.fields.msg)
        self.assertEqual(self.wid.fields.mail_to, ['lbt@example.com'])
        self.assertFalse(self.wid.fields.mail_cc)
        self.assertTrue(self.wid.result)

    def test_unknown_project(self):
        self.wid.params.maintainers_of = 'Project:Area51'
        self.assertRaises(urllib2.HTTPError,
                          self.participant.handle_wi, self.wid)
        self.assertFalse(self.wid.fields.mail_to)
        self.assertFalse(self.wid.fields.mail_cc)
        self.assertFalse(self.wid.result)

    def test_cc(self):
        self.wid.params.users = ['lbt', 'rbraakma']
        self.wid.params.cc = 'True'
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.fields.mail_to)
        self.assertEqual(sorted(self.wid.fields.mail_cc),
            ['lbt@example.com', 'rbraakma@example.com'])
        self.assertTrue(self.wid.result)

    def test_merge_mail_to(self):
        self.wid.params.users = ['lbt', 'rbraakma']
        self.wid.fields.mail_to = ['user1@example.com']
        self.participant.handle_wi(self.wid)
        self.assertEqual(sorted(self.wid.fields.mail_to),
            ['lbt@example.com', 'rbraakma@example.com', 'user1@example.com'])
        self.assertFalse(self.wid.fields.mail_cc)
        self.assertTrue(self.wid.result)

    def test_merge_mail_cc(self):
        self.wid.params.users = ['lbt', 'rbraakma']
        self.wid.params.cc = 'True'
        self.wid.fields.mail_cc = ['user1@example.com']
        self.participant.handle_wi(self.wid)
        self.assertFalse(self.wid.fields.mail_to)
        self.assertEqual(sorted(self.wid.fields.mail_cc),
            ['lbt@example.com', 'rbraakma@example.com', 'user1@example.com'])
        self.assertTrue(self.wid.result)

if __name__ == '__main__':
    unittest.main()
