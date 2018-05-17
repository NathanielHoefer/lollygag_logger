from vl_logger import vlogfield
from datetime import datetime
from vl_logger.venums import VLogType
import unittest

class TestFieldCreation(unittest.TestCase):

    def test_correct_datetime_field(self):
        token = "2018-05-08 14:33:22.984875"
        datetime = vlogfield.Datetime(token)
        self.assertEqual(str(datetime), "2018-05-08 14:33:22.984875")

    def test_incorrect_datetime_field(self):
        token = "this is incorrect"
        with self.assertRaises(ValueError):
            vlogfield.Datetime(token)

    def test_get_pattern(self):
        pattern = " ".join(["\d{4}-\d{2}-\d{2}", "\d{2}:\d{2}:\d{2}\.\d{6}"])
        pattern = "".join(["^", pattern, "$"])
        self.assertEqual(vlogfield.Datetime.get_pattern(), pattern)

    def test_get_datetime(self):
        token = "2018-05-08 14:33:22.984875"
        datetime_field = vlogfield.Datetime(token)
        format = " ".join(["%Y-%m-%d", "%H:%M:%S.%f"])
        datetime_obj = datetime.strptime(token, format)
        self.assertEqual(datetime_field.get_datetime(), datetime_obj)

    def test_correct_type_field(self):
        type = vlogfield.Type(VLogType.DEBUG)
        self.assertEqual(type.get_type(), VLogType.DEBUG)
        self.assertEqual(str(type), "DEBUG")

    def test_incorrect_type_field(self):
        with self.assertRaises(ValueError):
            vlogfield.Type("Garbage")

if __name__ == '__main__':
    unittest.main()