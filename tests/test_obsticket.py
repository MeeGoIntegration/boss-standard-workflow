"""Unit tests for obsticket BOSS participant."""

import os, shutil

from ConfigParser import ConfigParser
from mock import Mock
from RuoteAMQP import Workitem
import unittest
import obsticket

TMP = "test_tmp"

class WorkQueueTestCase(unittest.TestCase):
    """Test case for obsticket.WorkQueue."""

    def setUp(self): # pylint: disable=C0103
        """Test setup."""
        os.mkdir(TMP)
        self.queuename = os.path.join(TMP, "wq")

    def tearDown(self): # pylint: disable=C0103
        """Test tear down."""
        shutil.rmtree(TMP)

    def test_constructor(self):
        """Test WorkQueue.__init__()"""
        # Test that pointers get created
        wqueue = obsticket.WorkQueue(self.queuename)
        self.assertTrue(os.path.exists(self.queuename + ".curr"))
        self.assertTrue(os.path.exists(self.queuename + ".tail"))

        # Test that they are read correctly
        open(self.queuename + ".curr", "w").write("1")
        open(self.queuename + ".tail", "w").write("2")
        wqueue = obsticket.WorkQueue(self.queuename)
        self.assertEqual(wqueue.curr, 1)
        self.assertEqual(wqueue.tail, 2)

    def test_operations(self):
        """Test WorkQueue operations."""
        wqueue = obsticket.WorkQueue(self.queuename)
        self.assertRaises(obsticket.QueueEmpty, wqueue.head)
        self.assertRaises(obsticket.QueueNoNext, wqueue.next)

        self.assertTrue(wqueue.add("work 1"))
        self.assertFalse(wqueue.add("work 2"))

        self.assertEqual(wqueue.head(), "work 1")
        self.assertEqual(wqueue.next(), "work 2")
        self.assertEqual(wqueue.head(), "work 2")
        self.assertRaises(obsticket.QueueEmpty, wqueue.next)


class ParticipantHandlerTestCase(unittest.TestCase):
    """Test case for obsticket.ParticipantHandler."""

    def setUp(self): # pylint: disable=C0103
        """Test setup."""
        os.mkdir(TMP)
        self.queuename = os.path.join(TMP, "wq")
        ctrl = Mock()
        ctrl.message = "start"
        ctrl.config = ConfigParser()
        ctrl.config.add_section("obsticket")
        ctrl.config.set("obsticket", "prjdir", TMP)
        self.participant = obsticket.ParticipantHandler()
        self.participant.handle_lifecycle_control(ctrl)

    def tearDown(self): # pylint: disable=C0103
        """Test tear down."""
        shutil.rmtree(TMP)

    def test_handle_wi_control(self):
        """Test ParticipantHandler.handle_wi_control() (dummy)"""
        self.participant.handle_wi_control(None)
        # Does nothing currently

    def test_send_to_engine(self):
        """Test ParticipantHandler.send_to_engine() (dummy)"""
        self.participant.send_to_engine(None)
        # Does nothing currently


    def test_handle_wi(self):
        """Test ParticipantHandler.handle_wi()"""
        # pylint: disable=E1101
        wid = Workitem(
                '{"fei": { "wfid": "x", "subid": "x", "expid": "x",'
                '          "engine_id": "x" },'
                ' "fields": { "params": {}, "debug_dump": true } }'
                )
        self.assertRaises(RuntimeError, self.participant.handle_wi, wid)
        self.assertFalse(wid.result)

        wid.params.lock_project = "test"
        wid.params.action = "get"
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)
        # First item should go forward
        self.assertFalse(wid.forget)

        # Second one is forgotten in the queue
        self.participant.handle_wi(wid)
        self.assertTrue(wid.forget)

        wid.params.forget = False
        wid.params.action = "release"
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

        wid = Workitem(
                '{"fei": { "wfid": "y", "subid": "x", "expid": "x",'
                '          "engine_id": "x" },'
                ' "fields": { "params": { "lock_project": "test",'
                                         '"action": "release" },'
                '"debug_dump": true } }'
                )

        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)
