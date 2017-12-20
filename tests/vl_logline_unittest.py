"""
=========================================================================================================
ValenceLogLine Unittest
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 11/30/2017
"""

import unittest

from lollygag_logger.vl_lollygag_logger import ValenceLogLine as LogLine


class TestDateToken(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.date, "2017-10-30")

    def test_bad_format(self):
        line = LogLine("201-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] re")
        self.assertEqual(line.date, "")


class TestTimeToken(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.time, "19:13:32.209878")

    def test_bad_format(self):
        line = LogLine("2017-10-30 19:13:32.20987 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.time, "")


class TestTypeTokenTitle(unittest.TestCase):

    def test_under_minimum(self):
        line = LogLine("=============================")
        self.assertEqual(line.type, "OTHER")
        self.assertEqual(line.original_line, "=============================")

    def test_long_equal(self):
        line = LogLine("===============================================================================")
        self.assertEqual(line.type, "TITLE")

    def test_at_minimum(self):
        line = LogLine("==============================")
        self.assertEqual(line.type, "TITLE")

    def test_four_equal(self):
        line = LogLine("====")
        self.assertEqual(line.type, "OTHER")

    def test_bad_begin(self):
        line = LogLine("bad=====")
        self.assertEqual(line.type, "OTHER")

    def test_bad_middle(self):
        line = LogLine("=====bad==")
        self.assertEqual(line.type, "OTHER")

    def test_bad_end(self):
        line = LogLine("=====bad")
        self.assertEqual(line.type, "OTHER")


class TestTypeTokenStep(unittest.TestCase):

    def test_under_minimum(self):
        line = LogLine("-----------------------------")
        self.assertEqual(line.type, "STEP")
        self.assertEqual(line.original_line, "-----------------------------")

    def test_long_equal(self):
        line = LogLine("-------------------------------------------------------------------------------")
        self.assertEqual(line.type, "STEP")

    def test_under_minimum(self):
        line = LogLine("------------------------------")
        self.assertEqual(line.type, "STEP")
        self.assertEqual(line.original_line, "------------------------------")

    def test_four_equal(self):
        line = LogLine("----")
        self.assertEqual(line.type, "OTHER")

    def test_bad_begin(self):
        line = LogLine("bad-----")
        self.assertEqual(line.type, "OTHER")

    def test_bad_middle(self):
        line = LogLine("-----bad--")
        self.assertEqual(line.type, "OTHER")

    def test_bad_end(self):
        line = LogLine("-----bad")
        self.assertEqual(line.type, "OTHER")


class TestTypeTokenDebug(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.type, "DEBUG")

    def test_bad_format(self):
        line = LogLine("201-10-30 19:13:32.209878 DEBG [valence:42] [MainProcess:MainThread] re")
        self.assertEqual(line.type, "OTHER")


class TestTypeTokenOther(unittest.TestCase):

    def test_empty_line(self):
        line = LogLine("")
        self.assertEqual(line.type, "OTHER")

    def test_missing_token(self):
        line = LogLine("201-10-30 19:13:32.209878 DEBG [valence:42] re")
        self.assertEqual(line.type, "OTHER")

    def test_incorrect_format_tokens(self):
        line = LogLine("x x x x x x")
        self.assertEqual(line.type, "OTHER")


class TestSourceToken(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.source, "[valence:42]")

    def test_no_colon_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence42] [MainProcess:MainThread] reco")
        self.assertEqual(line.source, "")

    def test_no_brackets_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG valence:42 [MainProcess:MainThread] reco")
        self.assertEqual(line.source, "")


class TestThreadToken(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.thread, "[MainProcess:MainThread]")

    def test_no_colon_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcessMainThread] reco")
        self.assertEqual(line.thread, "")

    def test_no_brackets_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] MainProcess:MainThread reco")
        self.assertEqual(line.thread, "")


class TestDetailsToken(unittest.TestCase):

    def test_correct_format(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco")
        self.assertEqual(line.details, "reco")

    def test_no_details_with_type(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] ")
        self.assertEqual(line.type, "DEBUG")
        self.assertEqual(line.details, "")


class TestStandardFormat(unittest.TestCase):

    def test_full_standard_format(self):
        log = "2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] reco"
        line = LogLine(log)
        self.assertTrue(line.standard_format)
        self.assertEqual(line.date, "2017-10-30")
        self.assertEqual(line.time, "19:13:32.209878")
        self.assertEqual(line.type, "DEBUG")
        self.assertEqual(line.source, "[valence:42]")
        self.assertEqual(line.thread, "[MainProcess:MainThread]")
        self.assertEqual(line.details, "reco")
        self.assertEqual(str(line), log)

    def test_full_standard_format_no_details(self):
        line = LogLine("2017-10-30 19:13:32.209878 DEBUG [valence:42] [MainProcess:MainThread] ")
        self.assertTrue(line.standard_format)
        self.assertEqual(line.date, "2017-10-30")
        self.assertEqual(line.time, "19:13:32.209878")
        self.assertEqual(line.type, "DEBUG")
        self.assertEqual(line.source, "[valence:42]")
        self.assertEqual(line.thread, "[MainProcess:MainThread]")
        self.assertEqual(line.details, "")

    def test_full_title(self):
        line = LogLine("=========================================================")
        self.assertFalse(line.standard_format)
        self.assertEqual(line.date, "")
        self.assertEqual(line.time, "")
        self.assertEqual(line.type, "TITLE")
        self.assertEqual(line.source, "")
        self.assertEqual(line.thread, "")
        self.assertEqual(line.details, "")
        self.assertEqual(line.original_line, "=========================================================")

    def test_not_sf(self):
        line = LogLine("Test Suite: Starting Teardown of TsBulkVolOperations")
        self.assertFalse(line.standard_format)
        self.assertEqual(line.date, "")
        self.assertEqual(line.time, "")
        self.assertEqual(line.type, "OTHER")
        self.assertEqual(line.source, "")
        self.assertEqual(line.thread, "")
        self.assertEqual(line.details, "")
        self.assertEqual(line.original_line, "Test Suite: Starting Teardown of TsBulkVolOperations")


if __name__ == "__main__":
    unittest.main()
