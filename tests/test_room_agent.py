import unittest
from pathlib import Path

from live.room_agent import parse, run


class ParseTest(unittest.TestCase):
    def test_strips_mention(self):
        self.assertEqual(parse("@gate issue C-A"), ["issue", "C-A"])

    def test_strips_markup_mention(self):
        self.assertEqual(parse('<a href="x">@gate</a> tag C-B S2'), ["tag", "C-B", "S2"])

    def test_first_line_only(self):
        self.assertEqual(parse("@gate status\nclose S2"), ["status"])

    def test_shell_text_is_just_words(self):
        self.assertEqual(parse("@gate status; rm -rf /"), ["status;", "rm", "-rf", "/"])

    def test_empty_and_unbalanced(self):
        self.assertIsNone(parse("@gate"))
        self.assertIsNone(parse('@gate "open'))

    def test_sample_is_held_back(self):
        self.assertIn("REFUSED", run(["sample"], Path(".")))


if __name__ == "__main__":
    unittest.main()
