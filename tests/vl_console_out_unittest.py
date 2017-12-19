"""
=========================================================================================================
ValenceConsoleOutput Unittest
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/2/2017
"""

import sys
import unittest
from cStringIO import StringIO

from lollygag_logger.vl_config_file import *
from lollygag_logger.vl_lollygag_logger import ValenceConsoleOutput as Output
from lollygag_logger.vl_lollygag_logger import ValenceLogLine as LogLine


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
        self.format_config = create_config_file(os.getcwd())

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
        os.remove(os.getcwd() + "/" + FORMAT_CONFIG_FILE_NAME)


class DisplayLogTypesFormatting(unittest.TestCase):

    def setUp(self):
        self.format_config = create_config_file(os.getcwd())
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "debug", "True")
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "info", "True")
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "step", "True")
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "title", "True")
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "warning", "True")
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "error", "True")
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "other", "True")

        with open("test_logs/test.log", "r") as test_log_file:
            self.test_lines = test_log_file.readlines()
        self.test_lines = [x for x in self.test_lines if x[0] is not "#" and x.strip() is not ""]

    def test_display_all(self):
        log_formatter = Output(LogLine, self.format_config)
        display_test_lines = self.test_lines[:7]
        output = []
        with Capturing(output) as output:
            for line in display_test_lines:
                log_formatter.format(line)
        self.assertTrue("" not in output)
        self.assertTrue(len(output) == 7)

    def test_hide_debug(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "debug", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[0])
        self.assertTrue(len(output) == 0)

    def test_hide_info(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "info", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[1])
        self.assertTrue(len(output) == 0)

    def test_hide_warning(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "warning", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[2])
        self.assertTrue(len(output) == 0)

    def test_hide_error(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "error", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[3])
        self.assertTrue(len(output) == 0)

    def test_hide_step(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "step", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[4])
        self.assertTrue(len(output) == 0)

    def test_hide_title(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "title", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[5])
        self.assertTrue(len(output) == 0)

    def test_hide_other(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "other", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[6])
        self.assertTrue(len(output) == 0)

    def test_hide_at2_debug(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "debug", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[23])
        self.assertTrue(len(output) == 0)

    def test_hide_at2_info(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_LOG_TYPES_SECT, "info", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[24])
        self.assertTrue(len(output) == 0)

    def tearDown(self):
        os.remove(os.getcwd() + "/" + FORMAT_CONFIG_FILE_NAME)


class DisplayFieldsFormatting(unittest.TestCase):

    def setUp(self):
        self.format_config = create_config_file(os.getcwd())
        self.format_config.set(DISPLAY_FIELDS_SECT, "date", "True")
        self.format_config.set(DISPLAY_FIELDS_SECT, "time", "True")
        self.format_config.set(DISPLAY_FIELDS_SECT, "type", "True")
        self.format_config.set(DISPLAY_FIELDS_SECT, "source", "True")
        self.format_config.set(DISPLAY_FIELDS_SECT, "thread", "True")
        self.format_config.set(DISPLAY_FIELDS_SECT, "details", "True")

        with open("test_logs/test.log", "r") as test_log_file:
            self.test_lines = test_log_file.readlines()
        self.test_lines = [x for x in self.test_lines if x[0] is not "#" and x.strip() is not ""]
        self.original_line = self.test_lines[7]

    def test_hide_all(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "date", "False")
        self.format_config.set(DISPLAY_FIELDS_SECT, "time", "False")
        self.format_config.set(DISPLAY_FIELDS_SECT, "type", "False")
        self.format_config.set(DISPLAY_FIELDS_SECT, "source", "False")
        self.format_config.set(DISPLAY_FIELDS_SECT, "thread", "False")
        self.format_config.set(DISPLAY_FIELDS_SECT, "details", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.original_line)
        self.assertTrue("" in output)
        self.assertTrue(len(output) == 1)

    def test_hide_date(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "date", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[7])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[8].strip())

    def test_hide_time(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "time", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[7])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[9].strip())

    def test_hide_type(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "type", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[7])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[10].strip())

    def test_hide_source(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "source", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[7])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[11].strip())

    def test_hide_thread(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "thread", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[7])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[12].strip())

    def test_hide_details(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "details", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[7])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[13].strip())

    def test_hide_at2_date(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "date", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[25])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[26].strip())

    def test_hide_at2_time(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "time", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[25])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[27].strip())

    def test_hide_at2_type(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "type", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[25])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[28].strip())

    def test_hide_at2_source(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "source", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[25])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[29].strip())

    def test_hide_at2_details(self):
        log_formatter = Output(LogLine, self.format_config)
        self.format_config.set(DISPLAY_FIELDS_SECT, "details", "False")
        output = []
        with Capturing(output) as output:
            log_formatter.format(self.test_lines[25])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[30].strip())

    def tearDown(self):
        os.remove(os.getcwd() + "/" + FORMAT_CONFIG_FILE_NAME)


class MaxLineFormatting(unittest.TestCase):

    def setUp(self):
        self.format_config = create_config_file(os.getcwd())
        self.log_formatter = Output(LogLine, self.format_config)

        with open("test_logs/test.log", "r") as test_log_file:
            self.test_lines = test_log_file.readlines()
        self.test_lines = [x for x in self.test_lines if x[0] is not "#" and x.strip() is not ""]

    def test_max_len(self):
        self.log_formatter.sect_lengths["max_line_len"] = "100"
        output = []
        with Capturing(output) as output:
            self.log_formatter.format(self.test_lines[21])
        self.assertTrue(len(output) == 1)
        self.assertEqual(output[0], self.test_lines[22].strip())

    def tearDown(self):
        os.remove(os.getcwd() + "/" + FORMAT_CONFIG_FILE_NAME)


if __name__ == "__main__":
    unittest.main()
