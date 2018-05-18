import unittest
from datetime import datetime

from vl_logger import vlogfield
from vl_logger.venums import VLogType


class TestFieldCreation(unittest.TestCase):

    def test_get_datetime(self):
        token = "2018-05-08 14:33:22.984875"
        datetime_field = vlogfield.Datetime(token)
        format = " ".join(["%Y-%m-%d", "%H:%M:%S.%f"])
        datetime_obj = datetime.strptime(token, format)
        self.assertEqual(datetime_field.get_datetime(), datetime_obj)

    def test_correct_tokens(self):
        dt_token = "2018-05-08 14:33:22.984875"
        type_token = VLogType.DEBUG
        source_token = "[res.core.absolute:636]"
        thread_token = "[MainProcess:MainThread]"
        details_token = "Sending HTTP POST request to server_url"

        datetime = vlogfield.Datetime(dt_token)
        self.assertEqual(str(datetime), "2018-05-08 14:33:22.984875")

        type = vlogfield.Type(type_token)
        self.assertEqual(type.get_type(), VLogType.DEBUG)
        self.assertEqual(str(type), "DEBUG")

        source = vlogfield.Source(source_token)
        self.assertEqual(str(source), source_token)
        self.assertEqual(source.get_module(), "res.core.absolute")
        self.assertEqual(source.get_line_number(), 636)

        thread = vlogfield.Thread(thread_token)
        self.assertEqual(str(thread), thread_token)
        self.assertEqual(thread.get_process(), "MainProcess")
        self.assertEqual(thread.get_thread(), "MainThread")

        details = vlogfield.Details(details_token)
        self.assertEqual(str(details), details_token)

    def test_incorrect_tokens(self):
        token = "Garbage"
        with self.assertRaises(ValueError):
            vlogfield.Datetime(token)
        with self.assertRaises(ValueError):
            vlogfield.Type("Garbage")
        with self.assertRaises(ValueError):
            vlogfield.Source("Garbage")
        with self.assertRaises(ValueError):
            vlogfield.Thread("Garbage")

    def test_get_patterns(self):
        base_pattern = ".*"
        dt_pattern = " ".join(["\d{4}-\d{2}-\d{2}", "\d{2}:\d{2}:\d{2}\.\d{6}"])
        dt_pattern = "".join(["^", dt_pattern, "$"])
        type_pattern = "^DEBUG$|^INFO$|^NOTICE$|^WARNING$|^ERROR$|^CRITICAL$"
        source_pattern = "^\[.*:.*\]$"
        thread_pattern = "^\[.*:.*\]$"

        self.assertEqual(vlogfield.LogField.get_pattern(), base_pattern)
        self.assertEqual(vlogfield.Datetime.get_pattern(), dt_pattern)
        self.assertEqual(vlogfield.Type.get_pattern(), type_pattern)
        self.assertEqual(vlogfield.Source.get_pattern(), source_pattern)
        self.assertEqual(vlogfield.Thread.get_pattern(), thread_pattern)


if __name__ == '__main__':
    unittest.main()