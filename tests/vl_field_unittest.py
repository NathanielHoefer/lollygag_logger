"""
=========================================================================================================
Valence LogField Unittest
=========================================================================================================
by Nathaniel Hoefer
"""

import datetime
import unittest
import mock

from bin.vl_console_module import DatetimeField
from bin.vl_console_module.enums import LogType, ValenceField, ColorType


class TestDatetimeField(unittest.TestCase):

    def test_valence_datetime_format(self):
        vl_date_str = "2018-01-31"
        vl_time_str = "15:46:37.1903"
        datetime_field = DatetimeField(vl_date_str, vl_time_str)
        self.assertEqual(str(datetime_field), "2018-01-31 15:46:37.190300")

    def test_at2_datetime_format(self):
        vl_date_str = "2018-01-31"
        vl_time_str = "15:46:37,190"
        datetime_field = DatetimeField(vl_date_str, vl_time_str)
        self.assertEqual(str(datetime_field), "2018-01-31 15:46:37.190000")

    def test_invalid_format(self):
        vl_date_str = "2018-0131"
        vl_time_str = "15:46:37.1903"
        datetime_field = DatetimeField(vl_date_str, vl_time_str)
        self.assertEqual(str(datetime_field), "")

    def test_display_only_date(self):
        vl_date_str = "2018-01-31"
        vl_time_str = "15:46:37.1903"
        datetime_field = DatetimeField(vl_date_str, vl_time_str, display_time=False)
        self.assertEqual(str(datetime_field), "2018-01-31")

    def test_display_only_time(self):
        vl_date_str = "2018-01-31"
        vl_time_str = "15:46:37.1903"
        datetime_field = DatetimeField(vl_date_str, vl_time_str, display_date=False)
        self.assertEqual(str(datetime_field), "15:46:37.190300")

    def test_local_timezone(self):
        vl_date_str = "2018-01-31"
        vl_time_str = "15:46:37.1903"
        datetime_field = DatetimeField(vl_date_str, vl_time_str, local_time_zone=True)
        self.assertEqual(str(datetime_field), "2018-01-31 09:46:37.190300")