"""
=========================================================================================================
ValenceLogLine Unittest
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 11/30/2017
"""

import datetime
import unittest

from bin.vl_console_module import ValenceLogLine as LogLine
from bin.vl_console_module.enums import LogType, ValenceField, ColorType


class TestDateToken(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.date[0], datetime.datetime(2017, 10, 30))
        self.assertEqual(line.get_field_str(ValenceField.DATE), "2017-10-30")

    def test_bad_format(self):
        line = LogLine("201-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] re")
        self.assertEqual(line.date, None)


class TestTimeToken(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.time[0], datetime.datetime(1900, 1, 1, 19, 13, 32, 209878))
        self.assertEqual(line.get_field_str(ValenceField.TIME), "19:13:32.209878")

    def test_bad_format(self):
        line = LogLine("2017-10-30 19:13:32.20987 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.time, None)


class TestTypeTokenTitle(unittest.TestCase):

    def test_under_minimum(self):
        line = LogLine("=============================")
        self.assertEqual(line.get_log_type(), LogType.OTHER)
        self.assertEqual(line.original_line, "=============================")

    def test_long_equal(self):
        line = LogLine("===============================================================================")
        self.assertEqual(line.get_log_type(), LogType.TITLE)

    def test_at_minimum(self):
        line = LogLine("==============================")
        self.assertEqual(line.get_log_type(), LogType.TITLE)

    def test_four_equal(self):
        line = LogLine("====")
        self.assertEqual(line.get_log_type(), LogType.OTHER)

    def test_bad_begin(self):
        line = LogLine("bad=====")
        self.assertEqual(line.get_log_type(), LogType.OTHER)

    def test_bad_middle(self):
        line = LogLine("=====bad==")
        self.assertEqual(line.get_log_type(), LogType.OTHER)

    def test_bad_end(self):
        line = LogLine("=====bad")
        self.assertEqual(line.get_log_type(), LogType.OTHER)


class TestTypeTokenStep(unittest.TestCase):

    def test_under_minimum(self):
        line = LogLine("-----------------------------")
        self.assertEqual(line.get_log_type(), LogType.OTHER)
        self.assertEqual(line.original_line, "-----------------------------")

    def test_long_equal(self):
        line = LogLine("-------------------------------------------------------------------------------")
        self.assertEqual(line.get_log_type(), LogType.STEP)

    def test_at_minimum(self):
        line = LogLine("------------------------------")
        self.assertEqual(line.get_log_type(), LogType.STEP)
        self.assertEqual(line.original_line, "------------------------------")

    def test_four_equal(self):
        line = LogLine("----")
        self.assertEqual(line.get_log_type(), LogType.OTHER)

    def test_bad_begin(self):
        line = LogLine("bad-----")
        self.assertEqual(line.get_log_type(), LogType.OTHER)

    def test_bad_middle(self):
        line = LogLine("-----bad--")
        self.assertEqual(line.get_log_type(), LogType.OTHER)

    def test_bad_end(self):
        line = LogLine("-----bad")
        self.assertEqual(line.get_log_type(), LogType.OTHER)


class TestTypeTokenDebug(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.get_log_type(), LogType.DEBUG)

    def test_bad_format(self):
        line = LogLine("201-10-30 19:13:32.209878 DEBG [valence:42] [MainProcess:MainThread] re")
        self.assertEqual(line.get_log_type(), LogType.OTHER)


class TestTypeTokenOther(unittest.TestCase):

    def test_empty_line(self):
        line = LogLine("")
        self.assertEqual(line.get_log_type(), LogType.OTHER)

    def test_missing_token(self):
        line = LogLine("201-10-30 19:13:32.209878 DEBG [valence:42] re")
        self.assertEqual(line.get_log_type(), LogType.OTHER)

    def test_incorrect_format_tokens(self):
        line = LogLine("x x x x x x")
        self.assertEqual(line.get_log_type(), LogType.OTHER)


class TestSourceToken(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.get_field_str(ValenceField.SOURCE), "[valence:42]")

    def test_no_colon_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence42] [MainProcess:MainThread] reco")
        self.assertEqual(line.get_field_str(ValenceField.SOURCE), None)

    def test_no_brackets_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG valence:42 [MainProcess:MainThread] reco")
        self.assertEqual(line.get_field_str(ValenceField.SOURCE), None)


class TestThreadToken(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.get_field_str(ValenceField.THREAD), "[MainProcess:MainThread]")

    def test_no_colon_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcessMainThread] reco")
        self.assertEqual(line.get_field_str(ValenceField.THREAD), None)

    def test_no_brackets_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] MainProcess:MainThread reco")
        self.assertEqual(line.get_field_str(ValenceField.THREAD), None)


class TestDetailsToken(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.get_field_str(ValenceField.DETAILS), "reco")

    def test_no_details_with_type(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] ")
        self.assertEqual(line.get_log_type(), LogType.DEBUG)
        self.assertEqual(line.get_field_str(ValenceField.DETAILS), None)


class TestStandardFormat(unittest.TestCase):

    def test_full_standard_format(self):
        log = "2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco"
        line = LogLine(log)
        self.assertTrue(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.DATE), "2017-10-30")
        self.assertEqual(line.get_field_str(ValenceField.TIME), "19:13:32.209878")
        self.assertEqual(line.get_log_type(), LogType.DEBUG)
        self.assertEqual(line.get_field_str(ValenceField.SOURCE), "[valence:42]")
        self.assertEqual(line.get_field_str(ValenceField.THREAD), "[MainProcess:MainThread]")
        self.assertEqual(line.get_field_str(ValenceField.DETAILS), "reco")

    def test_full_standard_format_no_details(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] ")
        self.assertTrue(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.DATE), "2017-10-30")
        self.assertEqual(line.get_field_str(ValenceField.TIME), "19:13:32.209878")
        self.assertEqual(line.get_log_type(), LogType.DEBUG)
        self.assertEqual(line.source, "[valence:42]")
        self.assertEqual(line.thread, "[MainProcess:MainThread]")
        self.assertEqual(line.details, None)

    def test_full_title(self):
        line = LogLine("=========================================================")
        self.assertFalse(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.DATE), None)
        self.assertEqual(line.get_field_str(ValenceField.TIME), None)
        self.assertEqual(line.get_log_type(), LogType.TITLE)
        self.assertEqual(line.get_field_str(ValenceField.SOURCE), None)
        self.assertEqual(line.get_field_str(ValenceField.THREAD), None)
        self.assertEqual(line.get_field_str(ValenceField.DETAILS), None)
        self.assertEqual(line.original_line, "=========================================================")

    def test_not_sf(self):
        line = LogLine("Test Suite: Starting Teardown of TsBulkVolOperations")
        self.assertFalse(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.DATE), None)
        self.assertEqual(line.get_field_str(ValenceField.TIME), None)
        self.assertEqual(line.get_log_type(), LogType.OTHER)
        self.assertEqual(line.get_field_str(ValenceField.SOURCE), None)
        self.assertEqual(line.get_field_str(ValenceField.THREAD), None)
        self.assertEqual(line.get_field_str(ValenceField.DETAILS), None)
        self.assertEqual(line.original_line, "Test Suite: Starting Teardown of TsBulkVolOperations")


class RemoveGetSetFields(unittest.TestCase):

    def test_to_string(self):
        log = "2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco"
        line = LogLine(log)
        self.assertTrue(line.standard_format)
        self.assertEqual(str(line), log)

    def test_remove_fields(self):
        log = "2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco"
        result = "19:13:32.209878 DEBUG [valence:42] reco"
        line = LogLine(log)
        line.remove_field(ValenceField.DATE)
        line.remove_field(ValenceField.THREAD)
        self.assertTrue(line.standard_format)
        self.assertEqual(str(line), result)

    def test_get_detail(self):
        log = "2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco"
        line = LogLine(log)
        self.assertTrue(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.DETAILS), "reco")

    def test_get_type(self):
        log = "2017-10-30 19:13:32.209878 WARNING [valence:42] [MainProcess:MainThread] reco"
        line = LogLine(log)
        self.assertTrue(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.TYPE), "WARN ")
        self.assertEqual(line.get_log_type(), LogType.WARNING)

    def test_set_source(self):
        log = "2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco"
        line = LogLine(log)
        line.set_field_str(ValenceField.SOURCE, "[main:64]")
        self.assertTrue(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.SOURCE), "[main:64]")

    def test_set_type(self):
        log = "2017-10-30 19:13:32.209878 WARNING [valence:42] [MainProcess:MainThread] reco"
        line = LogLine(log)
        line.set_field_str(ValenceField.TYPE, "INFO")
        self.assertTrue(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.TYPE), "INFO")
        self.assertEqual(line.get_log_type(), LogType.WARNING)


class CondenseColor(unittest.TestCase):

    def test_condense_at_len(self):
        log = '2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] Sending HT'
        line = LogLine(log)
        line.condense_field(ValenceField.DETAILS, condense_len=10, collapse_dict=False,
                            collapse_list=False, collapse_len=5)
        self.assertTrue(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.DETAILS), "Sending HT\x1b[0m")

    def test_condense_above_len(self):
        log = '2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] Sending HTT'
        line = LogLine(log)
        line.condense_field(ValenceField.DETAILS, condense_len=10, collapse_dict=False,
                            collapse_list=False, collapse_len=5)
        self.assertTrue(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.DETAILS), "Sending...\x1b[0m")

    def test_collapse_above_len(self):
        log = '2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] S{nding }T'
        line = LogLine(log)
        line.condense_field(ValenceField.DETAILS, condense_len=12, collapse_dict=True,
                            collapse_list=False, collapse_len=7)
        self.assertTrue(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.DETAILS), "S{nd...}T\x1b[0m")

    def test_collapse_at_len(self):
        log = '2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] Se{ding }T'
        line = LogLine(log)
        line.condense_field(ValenceField.DETAILS, condense_len=12, collapse_dict=True,
                            collapse_list=False, collapse_len=7)
        self.assertTrue(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.DETAILS), "Se{ding }T\x1b[0m")

    def test_collapse_and_condense(self):
        log = '2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] HTTP S{nding }T'
        line = LogLine(log)
        line.condense_field(ValenceField.DETAILS, condense_len=10, collapse_dict=True,
                            collapse_list=False, collapse_len=7)
        self.assertTrue(line.standard_format)
        self.assertEqual(line.get_field_str(ValenceField.DETAILS), "HTTP S{...\x1b[0m")

    def test_color_type(self):
        log = '2017-10-30 19:13:32.209878 WARNING [valence:42] [MainProcess:MainThread] HTTP'
        line = LogLine(log)
        line.color_field(ValenceField.TYPE, ColorType.WARNING)
        self.assertEqual(line.get_field_str(ValenceField.TYPE), ColorType.WARNING.value + "WARN " +
                         ColorType.END.value)


if __name__ == "__main__":
    unittest.main()
