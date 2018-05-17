from vl_logger import vlogfield
import unittest

class TestFieldCreation(unittest.TestCase):

    def test_correct_datetime_field(self):
        token = "2018-05-08 14:33:22.984875"
        datetime = vlogfield.DatetimeField(token)
        self.assertEqual(str(datetime), "2018-05-08 14:33:22.984875")

    def test_incorrect_datetime_field(self):
        token = "this is incorrect"
        with self.assertRaises(ValueError):
            vlogfield.DatetimeField(token)

    def test_get_pattern(self):
        pattern = " ".join(["\d{4}-\d{2}-\d{2}", "\d{2}:\d{2}:\d{2}\.\d{6}"])
        pattern = "".join(["^", pattern, "$"])
        self.assertEqual(vlogfield.DatetimeField.get_pattern(), pattern)


if __name__ == '__main__':
    unittest.main()