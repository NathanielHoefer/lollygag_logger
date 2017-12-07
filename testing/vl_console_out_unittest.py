"""
=========================================================================================================
ValenceConsoleOutput Unittest
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/2/2017
"""

from vl_lollygag_logger import ValenceConsoleOutput as Output
from vl_lollygag_logger import ValenceLogLine as LogLine
from vl_config_file import *
import os
import unittest

from cStringIO import StringIO
import sys


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout


class InitialFormatting(unittest.TestCase):

    def setUp(self):
        self.format_config = create_config_file()

    def test_initialization(self):
        log_formatter = Output(LogLine, self.format_config)
        self.assertTrue(log_formatter.log_line_cls is LogLine)
        self.assertTrue(len(log_formatter.format_config.sections()) > 0)

    def test_log_newline(self):
        log_formatter = Output(LogLine, self.format_config)
        output = []
        with Capturing(output) as output:
            log_formatter.format("\n")
            log_formatter.format("\n\n\n\\n\\n\\n\n\n\n\n\\n\\n\\n\\n\\n\\n")
        self.assertTrue(len(output) == 1)
        self.assertTrue(output[0] == "")

    def tearDown(self):
        os.remove(FORMAT_CONFIG_FILE_NAME)


# class DisplayFormatting(unittest.TestCase):
#
#     def setUp(self):
#         self.format_config = create_config_file()
#         self.format_config.set()
#
#     def test_initialization(self):
#         log_formatter = Output(LogLine, self.format_config)
#         self.assertTrue(log_formatter.log_line_cls is LogLine)
#         self.assertTrue(len(log_formatter.format_config.sections()) > 0)
#
#     def test_log_newline(self):
#         log_formatter = Output(LogLine, self.format_config)
#         output = []
#         with Capturing(output) as output:
#             log_formatter.format("\n")
#             log_formatter.format("\n\n\n\\n\\n\\n\n\n\n\n\\n\\n\\n\\n\\n\\n")
#         self.assertTrue(len(output) == 1)
#         self.assertTrue(output[0] == "")
#
#     def tearDown(self):
#         os.remove(FORMAT_CONFIG_FILE_NAME)


if __name__ == "__main__":
    unittest.main()
