import unittest

from RuoteAMQP.workitem import Workitem
from common_test_lib import WI_TEMPLATE
from boss.checks import CheckActionProcessor


class Dummy(object):
    @CheckActionProcessor("check_basic_method_success")
    def check_basic_method_success(self, action, wid):
        return True, None

    @CheckActionProcessor("check_basic_method_fail")
    def check_basic_method_fail(self, action, wid):
        return False, "this fails"

    @CheckActionProcessor("check_ext_method_success")
    def check_ext_method_success(self, action, wid, ext_param):
        return True, ext_param

    @CheckActionProcessor("check_ext_method_fail")
    def check_ext_method_fail(self, action, wid, ext_param):
        return False, ext_param

    @CheckActionProcessor("check_method_action_type", action_types=["delete"])
    def check_method_action_type(self, action, wid):
        return False, "this fails"

@CheckActionProcessor("check_function_success", action_idx=0, wid_idx=1)
def check_function_success(action, wid):
    return True, None

@CheckActionProcessor("check_function_fail", action_idx=0, wid_idx=1)
def check_function_fail(action, wid):
    return False, None

@CheckActionProcessor("check_function_kwargs", action_idx="action",
wid_idx="wid")
def check_function_kwargs(action, wid):
    return True, None


class TestCheckActionProcessor(unittest.TestCase):
    def setUp(self):
        self.wid = Workitem(WI_TEMPLATE)
        self.dummy = Dummy()
        self.action = {"sourcepackage": "pkg",
                "type": "submit"}

    def test_params(self):
        self.assertRaises(TypeError, self.dummy.check_basic_method_success,
                "foo", "bar")
        self.assertRaises(TypeError, self.dummy.check_basic_method_success,
                self.action, "bar")

    def test_methods(self):
        result, msg = self.dummy.check_basic_method_success(
                self.action, self.wid)
        self.assertTrue(result)
        result, msg = self.dummy.check_basic_method_fail(
                self.action, self.wid)
        self.assertFalse(result)
        self.assertTrue(msg in self.wid.fields.msg[-1])
        result, msg = self.dummy.check_ext_method_success(
                self.action, self.wid, "foobear")
        self.assertEqual(msg, "foobear")
        self.assertTrue("foobear" not in self.wid.fields.msg[-1])

        result, msg = self.dummy.check_method_action_type(
                self.action, self.wid)
        self.assertTrue(result)
        self.action["type"] = "delete"
        result, msg = self.dummy.check_method_action_type(
                self.action, self.wid)
        self.assertFalse(result)

    def test_functions(self):
        result, msg = check_function_success(self.action, self.wid)
        self.assertTrue(result)
        result, msg = check_function_fail(self.action, self.wid)
        self.assertFalse(result)

        result, msg = check_function_kwargs(action=self.action, wid=self.wid)
        self.assertTrue(result)

    def test_skip(self):
        self.wid.fields.package_conf = {
                "pkg": {"checks": {"check_basic_method_fail": "skip"}}
            }
        result, msg = self.dummy.check_basic_method_fail(self.action, self.wid)
        self.assertTrue(result)
        self.assertTrue("SKIPPED" in self.wid.fields.msg[-1])

    def test_warn(self):
        self.wid.fields.package_conf = {
                "pkg": {"checks": {"check_basic_method_fail": "warn"}}
            }
        result, msg = self.dummy.check_basic_method_fail(self.action, self.wid)
        self.assertTrue(result)
        self.assertTrue("WARNING" in self.wid.fields.msg[-1])

if __name__ == "__main__":
    unittest.main()
