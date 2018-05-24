import unittest

from vl_logger.vutils import VLogType
from vl_logger.vutils import VPatterns

class TestGetType(unittest.TestCase):

    def test_get_type(self):
        line = "2017-10-30 19:13:32.208116 DEBUG [res.core:636] " \
               "[MainProcess:MainThread] Sending HTTP POST request"
        self.assertEqual(VLogType.get_type(line), VLogType.DEBUG)

        line = "2017-10-30 19:13:32.208116 INFO [res.core:636] " \
               "[MainProcess:MainThread] Sending HTTP POST request"
        self.assertEqual(VLogType.get_type(line), VLogType.INFO)

        line = "2017-10-30 19:13:32.208116 NOTICE [res.core:636] " \
               "[MainProcess:MainThread] Sending HTTP POST request"
        self.assertEqual(VLogType.get_type(line), VLogType.NOTICE)

        line = "2017-10-30 19:13:32.208116 WARNING [res.core:636] " \
               "[MainProcess:MainThread] Sending HTTP POST request"
        self.assertEqual(VLogType.get_type(line), VLogType.WARNING)

        line = "2017-10-30 19:13:32.208116 ERROR [res.core:636] " \
               "[MainProcess:MainThread] Sending HTTP POST request"
        self.assertEqual(VLogType.get_type(line), VLogType.ERROR)

        line = "2017-10-30 19:13:32.208116 CRITICAL [res.core:636] " \
               "[MainProcess:MainThread] Sending HTTP POST request"
        self.assertEqual(VLogType.get_type(line), VLogType.CRITICAL)


class TestGetPatterns(unittest.TestCase):

    def test_get_std(self):

        pattern = " ".join([
            "\d{4}-\d{2}-\d{2}",
            "\d{2}:\d{2}:\d{2}\.\d{6}",
            "(DEBUG|INFO|NOTICE|WARNING|ERROR|CRITICAL)",
            "\[.*:.*\]",
            "\[.*:.*\]",
            ".*"
        ])
        self.assertEqual(VPatterns.get_std(), pattern)

        def test_get_patterns(self):
            dt_pattern = " ".join(
                ["\d{4}-\d{2}-\d{2}", "\d{2}:\d{2}:\d{2}\.\d{6}"])
            type_pattern = "(DEBUG|INFO|NOTICE|WARNING|ERROR|CRITICAL)"
            source_pattern = "\[.*:.*\]"
            thread_pattern = "\[.*:.*\]"
            details_pattern= ".*"

            self.assertEqual(VPatterns.get_std_datetime(), dt_pattern)
            self.assertEqual(VPatterns.get_std_type(), type_pattern)
            self.assertEqual(VPatterns.get_std_source(), source_pattern)
            self.assertEqual(VPatterns.get_std_thread(), thread_pattern)
            self.assertEqual(VPatterns.get_std_details(), details_pattern)


if __name__ == '__main__':
    unittest.main()