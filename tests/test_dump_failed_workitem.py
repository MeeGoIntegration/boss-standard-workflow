from mock import Mock

import unittest
import os
from tempfile import mkdtemp
import shutil

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
        self.participant.workitem_path = mkdtemp()
        self.assertRaises(RuntimeError,self.participant.handle_wi, wid)

        wid = Workitem(BASE_WORKITEM)
        wid.result = False
        wid.fields.ev.id = "1"
        wid.fields.ev.project = "Project:Trunk"
        wid.fields.ev.type = "OBS_REPO_PUBLISHED"
        wid.fields.ev.time = "1316946975"
        workitem_test_filename = os.path.join(self.participant.workitem_path,
                                              "Project:Trunk_1316946975_SR-#1-OBS_REPO_PUBLISHED"
                                             )
        self.participant.handle_wi(wid)
        self.assertTrue(wid.fields.workitem_filename)
        self.assertTrue(wid.fields.workitem_filename != "")
        self.assertTrue(wid.fields.workitem_filename == workitem_test_filename)

        if os.path.exists(self.participant.workitem_path):
            shutil.rmtree(self.participant.workitem_path)

    def test_write_workitem(self):
        wid = Workitem(BASE_WORKITEM)
        wid.result = True
        self.assertRaises(RuntimeError, self.participant.write_workitem, wid)
        wid.fields.debug_dump = True
        wid.result = False
        wid.fields.ev.id = "1"
        wid.fields.ev.project = "Project:Trunk"
        wid.fields.ev.type = "OBS_REPO_PUBLISHED"
        wid.fields.ev.time = "1316946975"
        self.participant.workitem_path = mkdtemp()

        workitem_path = self.participant.write_workitem(wid)
        self.assertTrue(os.path.exists(workitem_path))
        self.assertTrue(workitem_path != "")
        workitem_test_filename = os.path.join(self.participant.workitem_path,
                                      "Project:Trunk_1316946975_SR-#1-OBS_REPO_PUBLISHED"
                                     )
        self.assertTrue(workitem_path == workitem_test_filename)

        workitem_text = open(workitem_path).read()
        self.assertEquals(workitem_text, wid.dump())

        if os.path.exists(workitem_path):
            shutil.rmtree(os.path.dirname(workitem_path))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
