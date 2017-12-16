"""
=========================================================================================================
ValenceHeader Unittest
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/2/2017
"""

from vl_lollygag_logger import ValenceConsoleOutput as Output
from vl_lollygag_logger import ValenceLogLine as LogLine
from vl_lollygag_logger import ValenceHeader
from vl_config_file import *
from vl_console_out_unittest import Capturing
import os
import unittest

from cStringIO import StringIO
import sys


class TitleParse(unittest.TestCase):

    def setUp(self):
        with open("test.log", "r") as test_log_file:
            self.test_lines = test_log_file.readlines()
        self.test_lines = [x for x in self.test_lines if x[0] is not "#" and x.strip() is not ""]

    def test_case_title(self):
        original_line = "Test Case 1: Starting Teardown of TcGenericTestCase"
        header = ValenceHeader(original_line, "title")
        self.assertFalse(header.suite)
        self.assertEqual(header.test_name, "TcGenericTestCase")
        self.assertEqual(header.test_info, "Test Case 1")
        self.assertEqual(header.test_instruction, "Starting Teardown of TcGenericTestCase")
        self.assertEqual(header.test_number, 1)

    def test_suite_title(self):
        original_line = "Test Suite: Starting Teardown of TsGenericTestSuite"
        header = ValenceHeader(original_line, "title")
        self.assertTrue(header.suite)
        self.assertEqual(header.test_name, "TsGenericTestSuite")
        self.assertEqual(header.test_info, "Test Suite")
        self.assertEqual(header.test_instruction,
                         "Starting Teardown of TsGenericTestSuite")
        self.assertEqual(header.test_number, 0)

    def test_other_title(self):
        original_line = "All Test Case Preconditions"
        header = ValenceHeader(original_line, "title")
        self.assertFalse(header.suite)
        self.assertEqual(header.test_name, "")
        self.assertEqual(header.test_info, "")
        self.assertEqual(header.test_instruction, "")
        self.assertEqual(header.test_number, 0)

    def test_case_step(self):
        original_line = "Starting Step 2 for TcGenericTestCase: Completed Monitoring"
        header = ValenceHeader(original_line, "step")
        self.assertFalse(header.suite)
        self.assertEqual(header.test_name, "TcGenericTestCase")
        self.assertEqual(header.test_info, "Starting Step 2 for TcGenericTestCase")
        self.assertEqual(header.test_instruction, "Completed Monitoring")
        self.assertEqual(header.test_number, 2)


# class HeaderParse(unittest.TestCase):
#
#     def setup(self):
#         self.format_config = create_config_file(os.getcwd())
#         self.log_formatter = Output(LogLine, self.format_config)
#
#         with open("test.log", "r") as test_log_file:
#             self.test_lines = test_log_file.readlines()
#         self.test_lines = [x for x in self.test_lines if x[0] is not "#" and x.strip() is not ""]
#
#     def test_title_parse(self):
#         multi_line_title = [self.test_lines[5], self.test_lines[6], self.test_lines[5]]
#         output = []
#         with Capturing(output) as output:
#             for line in multi_line_title:
#                 self.log_formatter.format(line)
#
#         self.assertEqual(multi_line_title, output)
#
#     def tearDown(self):
#         os.remove(os.getcwd() + "/" + FORMAT_CONFIG_FILE_NAME)


if __name__ == "__main__":
    unittest.main()
