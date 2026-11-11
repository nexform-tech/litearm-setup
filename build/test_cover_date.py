"""Tests for the cover-date substitution."""

import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cover_date import en, stamp, zh  # noqa: E402


class FormatTest(unittest.TestCase):
    def test_chinese_date(self):
        self.assertEqual(zh(datetime.date(2026, 11, 11)), "2026年11月11日")
        self.assertEqual(zh(datetime.date(2026, 1, 5)), "2026年1月5日")

    def test_english_date(self):
        self.assertEqual(en(datetime.date(2026, 11, 11)), "11 November 2026")
        self.assertEqual(en(datetime.date(2026, 3, 1)), "1 March 2026")


class StampTest(unittest.TestCase):
    def test_both_tokens_are_filled(self):
        text = ("版本：V1.1\\qquad 日期：@COVERDATE_ZH@\n"
                "Version 1.1\\qquad @COVERDATE_EN@")
        now = datetime.datetime(2026, 11, 11, 9, 0,
                                tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
        self.assertEqual(
            stamp(text, now),
            "版本：V1.1\\qquad 日期：2026年11月11日\n"
            "Version 1.1\\qquad 11 November 2026")

    def test_a_utc_evening_becomes_the_next_day_in_beijing(self):
        now = datetime.datetime(2026, 11, 10, 18, 0,
                                tzinfo=datetime.timezone.utc)
        self.assertEqual(stamp("@COVERDATE_ZH@", now), "2026年11月11日")

    def test_text_without_tokens_is_untouched(self):
        self.assertEqual(stamp("# 前言\n"), "# 前言\n")


if __name__ == "__main__":
    unittest.main()
