import unittest

from RuoteAMQP.workitem import Workitem
from common_test_lib import WI_TEMPLATE
import boss
from boss.checks import CheckActionProcessor


class Dummy(object):
    @CheckActionProcessor("check_method")
    def check_method(self, action, wid, success=True, message=None):
        return success, message

    @CheckActionProcessor("check_method_action_type", action_types=["delete"])
    def check_method_action_type(self, action, wid):
        return False, "this fails"

@CheckActionProcessor("check_function", action_idx=0, wid_idx=1)
def check_function(action, wid, success=True, message=None):
    return success, message

@CheckActionProcessor("check_function_kwargs", action_idx="action",
wid_idx="wid")
def check_function_kwargs(success=True, message=None, action=None, wid=None):
    return success, message


class TestCheckActionProcessor(unittest.TestCase):
    def setUp(self):
        self.wid = Workitem(WI_TEMPLATE)
        self.dummy = Dummy()
        self.action = {"sourcepackage": "pkg",
                "type": "submit"}

    def test_param_types(self):
        self.assertRaises(TypeError, self.dummy.check_method,
                "foo", "bar")
        self.assertRaises(TypeError, self.dummy.check_method,
                self.action, "bar")

    def test_action_type(self):
        result, msg = self.dummy.check_method_action_type(self.action, self.wid)
        self.assertTrue(result)
        self.assertTrue("Unsupported action type" in msg)
        self.action["type"] = "delete"
        result, msg = self.dummy.check_method_action_type(self.action, self.wid)
        self.assertFalse(result)

    def test_no_package(self):
        self.action.pop("sourcepackage")
        result, msg = self.dummy.check_method(self.action, self.wid,
                success=True, message="my own message")
        self.assertTrue(result)
        self.assertEqual(msg, "my own message")
        self.assertEqual(len(self.wid.fields.msg), 0)

    def test_param_index(self):
        result, msg = check_function(self.action, self.wid, True, "foobear")
        self.assertTrue(result)
        self.assertTrue("foobear" in self.wid.fields.msg[-1])
        self.wid.fields.msg = []

        result, msg = check_function_kwargs(action=self.action, wid=self.wid,
                success=True, message="foobear")
        self.assertTrue(result)
        self.assertTrue("foobear" in self.wid.fields.msg[-1])

    def test_skip(self):
        self.wid.fields.package_conf = {
                "pkg": {"checks": {"check_method": "skip"}}
            }
        result, msg = self.dummy.check_method(self.action, self.wid,
                success=False)
        self.assertTrue(result)
        self.assertTrue("SKIPPED" in self.wid.fields.msg[-1])
        result, msg = self.dummy.check_method(self.action, self.wid,
                message="foobear")
        self.assertFalse("foobear" in self.wid.fields.msg[-1])

    def test_warn(self):
        self.wid.fields.package_conf = {
                "pkg": {"checks": {"check_method": "warn"}}
            }

        result, msg = self.dummy.check_method(self.action, self.wid,
                success=False)
        self.assertTrue(result)
        self.assertTrue("WARNING" in self.wid.fields.msg[-1])

        result, msg = self.dummy.check_method(self.action, self.wid,
                success=True, message="foobear")
        self.assertTrue(result)
        self.assertTrue("foobear" in self.wid.fields.msg[-1])

    def test_verbose(self):
        self.wid.fields.package_conf = {
                "pkg": {"checks": {"check_method": "verbose"}}
            }

        result, msg = self.dummy.check_method(self.action, self.wid,
                success=False)
        self.assertFalse(result)
        self.assertTrue("FAILED" in self.wid.fields.msg[-1])

        result, msg = self.dummy.check_method(self.action, self.wid,
                success=True, message="foobear")
        self.assertTrue(result)
        self.assertTrue("SUCCESS" in self.wid.fields.msg[-1])
        self.assertTrue("foobear" in self.wid.fields.msg[-1])

    def test_quiet(self):
        self.wid.fields.package_conf = {
                "pkg": {"checks": {"check_method": "quiet"}}
            }

        result, msg = self.dummy.check_method(self.action, self.wid,
                success=True, message="foobear")
        self.assertTrue(result)
        self.assertEqual(len(self.wid.fields.msg), 0)

        result, msg = self.dummy.check_method(self.action, self.wid,
                success=False)
        self.assertFalse(result)
        self.assertTrue("FAILED" in self.wid.fields.msg[-1])

    def test_bad_level(self):
        self.wid.fields.package_conf = {
                "pkg": {"checks": {"check_method": "foo"}}
            }
        result, msg = self.dummy.check_method(self.action, self.wid,
                success=True, message="foobear")
        self.assertEqual(len(self.wid.fields.msg), 2)
        self.assertTrue("Unknown check level" in self.wid.fields.msg[0])


if __name__ == "__main__":
    unittest.main()
