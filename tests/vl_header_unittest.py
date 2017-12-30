"""
=========================================================================================================
ValenceHeader Unittest
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/19/2017
"""

import unittest
from bin.vl_console_module import ValenceHeader, ValenceLogLine, ValenceConsoleFormatter
from bin.vl_console_module.vl_config_file import *
from bin.lollygag_logger import LollygagLogger
from bin.vl_console_module.enums import *


class HeaderParse(unittest.TestCase):

    def setUp(self):
        with open("test_logs/test.log", "r") as test_log_file:
            self.test_lines = test_log_file.readlines()
        self.test_lines = [x for x in self.test_lines if x[0] is not "#" and x.strip() is not ""]

    def test_case_title(self):
        original_line = "Test Case 1: Starting Teardown of TcGenericTestCase"
        header = ValenceHeader(original_line)
        self.assertEqual(header.header_type, HeaderType.TEST_CASE)
        self.assertEqual(header.test_name, "TcGenericTestCase")
        self.assertEqual(header.test_info, "Test Case 1")
        self.assertEqual(header.test_instruction, "Starting Teardown of TcGenericTestCase")
        self.assertEqual(header.test_number, 1)

    def test_suite_title(self):
        original_line = "Test Suite: Starting Teardown of TsGenericTestSuite"
        header = ValenceHeader(original_line)
        self.assertEqual(header.header_type, HeaderType.SUITE)
        self.assertEqual(header.test_name, "TsGenericTestSuite")
        self.assertEqual(header.test_info, "Test Suite")
        self.assertEqual(header.test_instruction,
                         "Starting Teardown of TsGenericTestSuite")
        self.assertEqual(header.test_number, 0)

    def test_other_title(self):
        original_line = "All Test Case Preconditions"
        header = ValenceHeader(original_line)
        self.assertEqual(header.header_type, HeaderType.VALENCE)
        self.assertEqual(header.test_name, "")
        self.assertEqual(header.test_info, "")
        self.assertEqual(header.test_instruction, "")
        self.assertEqual(header.test_number, 0)

    def test_case_step(self):
        original_line = "Starting Step 2 for TcGenericTestCase: Completed Monitoring"
        header = ValenceHeader(original_line)
        self.assertEqual(header.header_type, HeaderType.STEP)
        self.assertEqual(header.test_name, "TcGenericTestCase")
        self.assertEqual(header.test_info, "Starting Step 2 for TcGenericTestCase")
        self.assertEqual(header.test_instruction, "Completed Monitoring")
        self.assertEqual(header.test_number, 2)

    # def test_store_header(self):
    #
    #     config_file = create_config_file()
    #     vl_console_output = ValenceConsoleFormatter(ValenceLogLine, config_file,
    #                                                 list_step="Test Case 0: Starting Test of "
    #                                                           "TcBulkVolSFtoSFS3Swift")
    #     with open("/home/nathaniel/Downloads/test.log", "r") as logfile:
    #         logger = LollygagLogger(logfile, vl_console_output)
    #         logger.run()


if __name__ == "__main__":
    unittest.main()
