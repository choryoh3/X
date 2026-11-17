import unittest
import helpers
from clean_srt import clean_srt


class CleanSrt(unittest.TestCase):
    def test_removes_timecodes_numbers_and_rolling_duplicates(self):
        self.assertEqual(clean_srt(helpers.SRT), "こんにちは 今日は字幕の話です\n")

    def test_empty(self):
        self.assertEqual(clean_srt("1\n00:00:01,000 --> 00:00:02,000\n\n"), "")


if __name__ == "__main__":
    unittest.main()
