import unittest

from app.utils.utils import pass_fail


class TestSkygridOnDemand(unittest.TestCase):

    def test_pass_fail_with_true(self):
        self.assertEqual(pass_fail(True), 'PASS')

    def test_pass_fail_with_false(self):
        self.assertEqual(pass_fail(False), 'FAIL')

    def test_pass_fail_with_none(self):
        self.assertEqual(pass_fail(None), 'UNKNOWN')