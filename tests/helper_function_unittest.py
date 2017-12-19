"""
=========================================================================================================
Helpers Unittest
=========================================================================================================
by Nathaniel Hoefer
Last Updated: 12/2/2017
"""

import unittest
from lollygag_logger.helpers import *


class StrToBool(unittest.TestCase):

    def test_str_to_bool(self):
        self.assertTrue(str_to_bool("True"))
        self.assertTrue(str_to_bool("true"))
        self.assertTrue(str_to_bool("Yes"))
        self.assertTrue(str_to_bool("yes"))
        self.assertTrue(str_to_bool("T"))
        self.assertTrue(str_to_bool("t"))
        self.assertTrue(str_to_bool("Y"))
        self.assertTrue(str_to_bool("y"))
        self.assertTrue(str_to_bool("1"))

        self.assertFalse(str_to_bool("False"))
        self.assertFalse(str_to_bool("false"))
        self.assertFalse(str_to_bool("F"))
        self.assertFalse(str_to_bool("f"))
        self.assertFalse(str_to_bool("No"))
        self.assertFalse(str_to_bool("no"))
        self.assertFalse(str_to_bool("N"))
        self.assertFalse(str_to_bool("n"))
        self.assertFalse(str_to_bool("0"))
        self.assertFalse(str_to_bool("asdfasdf"))
        self.assertFalse(str_to_bool(""))


class CollapseStructFormatting(unittest.TestCase):

    def setUp(self):
        self.collapsed_len = 30

    def test_collapse_empty_list(self):
        self.assertEqual(collapse_struct("[]", "list"), "[]")

    def test_collapse_empty_dict(self):
        self.assertEqual(collapse_struct("{}", "dict"), "{}")

    def test_collapse_at_len_list(self):
        self.assertEqual(collapse_struct("[abcdefghijklmnopqrstuvwxyzab]", "list", self.collapsed_len),
                         "[abcdefghijklmnopqrstuvwxyzab]")

    def test_collapse_at_len_dict(self):
        self.assertEqual(collapse_struct("{abcdefghijklmnopqrstuvwxyzab}", "dict", self.collapsed_len),
                         "{abcdefghijklmnopqrstuvwxyzab}")

    def test_collapse_one_over(self):
        self.assertEqual(collapse_struct("[abcdefghijklmnopqrstuvwxyzabc]", "list", self.collapsed_len),
                         "[abcdefghijklmnopqrstuvwxy...]")

    def test_collapse_no_list(self):
        self.assertEqual(collapse_struct("abcdefghijklmnopqrstuvwxyzabcdef", "list", self.collapsed_len),
                         "abcdefghijklmnopqrstuvwxyzabcdef")


class CondenseFieldsFormatting(unittest.TestCase):

    def setUp(self):

        self.collapse_dict = True
        self.collapse_list = True
        self.collapse_len = 30
        self.condense_len = 100

        with open("test_logs/test.log", "r") as test_log_file:
            self.test_lines = test_log_file.readlines()
        self.test_lines = [x for x in self.test_lines if x[0] is not "#" and x.strip() is not ""]

    def test_at_len_no_struct(self):
        condensed_str = condense_field(self.test_lines[14].strip(), self.condense_len,
                                       self.collapse_dict, self.collapse_list, self.collapse_len)
        self.assertEqual(condensed_str, self.test_lines[14].strip())

    def test_at_len_struct(self):
        condensed_str = condense_field(self.test_lines[15].strip(), self.condense_len,
                                       self.collapse_dict, self.collapse_list, self.collapse_len)
        self.assertEqual(condensed_str, self.test_lines[16].strip())

    def test_one_over_len(self):
        condensed_str = condense_field(self.test_lines[17].strip(), self.condense_len,
                                       self.collapse_dict, self.collapse_list, self.collapse_len)
        self.assertEqual(condensed_str, self.test_lines[18].strip())

    def test_over_len_no_struct_collapse(self):
        self.collapse_dict = False
        condensed_str = condense_field(self.test_lines[19].strip(), self.condense_len,
                                       self.collapse_dict, self.collapse_list, self.collapse_len)
        self.assertEqual(condensed_str, self.test_lines[20].strip())


if __name__ == "__main__":
    unittest.main()
