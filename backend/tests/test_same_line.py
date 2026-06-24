import unittest
from app.services.documents import extract_same_line_value

class TestSameLine(unittest.TestCase):
    def test_basic_same_line(self):
        line = "Owner Name: John Doe"
        res = extract_same_line_value("Owner Name", line, 0)
        self.assertIsNotNone(res)
        self.assertEqual(res["value"], "John Doe")
        self.assertEqual(res["matched_label"], "Owner Name")
        self.assertEqual(res["match_type"], "same_line")
        self.assertEqual(res["source_line"], 1)

    def test_multiple_separators(self):
        # Testing different separators like dash, equals
        self.assertEqual(extract_same_line_value("Age", "Age - 35", 0)["value"], "35")
        self.assertEqual(extract_same_line_value("Age", "Age = 35", 0)["value"], "35")
        self.assertEqual(extract_same_line_value("Age", "Age: 35", 0)["value"], "35")

    def test_no_value(self):
        line = "Owner Name:"
        res = extract_same_line_value("Owner Name", line, 0)
        self.assertIsNone(res)

if __name__ == "__main__":
    unittest.main()
