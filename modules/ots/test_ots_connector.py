import unittest

from mock import Mock
from ots_connector import parse_options, call_ots_server

class TestOtsConnector(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_options(self):
        workitem = WorkitemMock()

        result = parse_options(workitem)

    def test_call_ots_server_debug(self):
        result = call_ots_server("server",
                                 "sw_product",
                                 "build_id",
                                 [],
                                 {},
                                 True)
        self.assertEquals(result, "ERROR")

    def test_call_ots_server(self):
        result = call_ots_server("server",
                                 "sw_product",
                                 "build_id",
                                 [],
                                 {},
                                 False,
                                 xmlrpcMock())
        self.assertEquals(result, "PASS")

    def test_call_ots_server_no_interface(self):
        import xmlrpclib
        xmlrpclib.Server = Mock()
        xmlrpclib.Server.return_value = xmlrpcMock()
        result = call_ots_server("server",
                                 "sw_product",
                                 "build_id",
                                 [],
                                 {},
                                 False)
        self.assertEquals(result, "PASS")


class xmlrpcMock(object):
    def __init__(self):
        self.called = False
    def request_sync(self, sw_product, build_id, email_list, options):
        self.called = True
        return "PASS"

class WorkitemMock(object):
    def __init__(self):
        self.fields = Mock()
        self.fields.product = "dummyproduct"
        self.fields.rid = "715517"
        self.fields.emails = ["dummy@email"]
        self.fields.image.image_url = "http://dummy/image"
        self.fields.image.devicegroup = "devicegroup:dummy_devicegroup"
        self.fields.image.test_options.as_dict.return_value = {}

    def set_field(self, key, value):
        self.data[key] = value

if __name__ == '__main__':
    unittest.main()

