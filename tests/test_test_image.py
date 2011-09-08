import unittest

from mock import Mock

import test_image

class TestParticipantHandler(unittest.TestCase):

    def setUp(self):
        test_image.ots = Mock()
        test_image.ots.ots_connector.parse_options.return_value = \
                ("", "", [], {})

        self.participant = test_image.ParticipantHandler()

    def test_handle_wi_control(self):
        self.participant.handle_wi_control(None)

    def test_handle_lifecycle_control(self):
        ctrl = Mock
        ctrl.message = "start"
        ctrl.config = Mock()
        self.participant.handle_lifecycle_control(ctrl)

    def test_handle_wi(self):
        wid = Mock()
        wid.fields.debug = "True"
        wid.fields.msg = None
        test_image.ots.ots_connector.call_ots_server.return_value = "FAIL"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

        test_image.ots.ots_connector.call_ots_server.return_value = "PASS"
        wid.params.enforce = "False"
        self.participant.handle_wi(wid)
        self.assertTrue(wid.result)

        test_image.ots.ots_connector.call_ots_server.return_value = "FAIL"
        wid.params.enforce = "True"
        self.participant.handle_wi(wid)
        self.assertFalse(wid.result)

if __name__ == '__main__':
    unittest.main()
