from mock import Mock

import unittest
import os

from common_test_lib import BaseTestParticipantHandler
from RuoteAMQP import Workitem

BASE_WORKITEM = '{"fei": 1, "fields": {"params": {}, "msg": [],"ev": {"actions": []} }, "project":"Some:Target"}'


class TestParticipantHandler(BaseTestParticipantHandler):

    module_under_test = "dump_failed_workitem"

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_handle_wi(self):
        wid = Workitem(BASE_WORKITEM)
        wid.result = False
        self.participant.handle_wi(wid)

    def test_write_workitem(self):
        wid = Workitem(BASE_WORKITEM)
        wid.result = False
        wid.fields.id = "1"
        wid.fields.project = "bleh"
        wid.fields.type = "sometype"
        wid.fields.time = "12212011"
        self.participant.workitem_path = "/tmp/"

        workitem_path = self.participant.write_workitem(wid)
        self.assertTrue(os.path.exists(workitem_path))
        self.assertTrue(workitem_path != "")

        workitem_text = open(workitem_path).read()
        self.assertEquals(workitem_text, wid.dump())

        if os.path.exists(workitem_path):
            os.remove(workitem_path)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
