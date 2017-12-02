"""
=========================================================================================================
ValenceConsoleOutput Unittest
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/2/2017
"""

from vl_lollygag_logger import ValenceConsoleOutput as Output
from vl_lollygag_logger import ValenceLogLine as LogLine
from vl_lollygag_logger import create_config_file
from vl_lollygag_logger import FORMAT_CONFIG_FILE_NAME
import os
import unittest


class Initialization(unittest.TestCase):

    def setUp(self):
        format_config = create_config_file()
        self.LogFormatter = Output(LogLine, format_config)

    def test_initialization(self):
        self.assertTrue(self.LogFormatter.log_line_cls is LogLine)
        self.assertTrue(len(self.LogFormatter.format_config.sections()) > 0)

    def tearDown(self):
        os.remove(FORMAT_CONFIG_FILE_NAME)


if __name__ == "__main__":
    unittest.main()