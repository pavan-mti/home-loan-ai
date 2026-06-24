import unittest
from app.services.documents import extract_multiline_value

class TestMultiline(unittest.TestCase):
    def test_multiline_joining(self):
        lines = [
            "Postal Address:",
            "Flat 502, GBR Barcelona,",
            "Puppalaguda, Hyderabad",
            "Survey No:"
        ]
        stop_aliases = ["Survey No"]
        res = extract_multiline_value(1, lines, stop_aliases)
        self.assertIsNotNone(res)
        self.assertIn("Flat 502, GBR Barcelona", res)
        self.assertIn("Puppalaguda, Hyderabad", res)
        self.assertNotIn("Survey No", res)

    def test_stop_trigger(self):
        lines = [
            "Line 1",
            "Line 2",
            "Stop Here: Yes"
        ]
        res = extract_multiline_value(0, lines, ["Stop Here"])
        self.assertEqual(res, "Line 1, Line 2")

if __name__ == "__main__":
    unittest.main()
