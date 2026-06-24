import unittest
from app.services.field_patterns import clean_name, clean_address_str, clean_generic

class TestCleaners(unittest.TestCase):
    def test_clean_name(self):
        self.assertEqual(clean_name("Mr. John Doe"), "John Doe")
        self.assertEqual(clean_name("Mrs. Jane Smith"), "Jane Smith")
        self.assertEqual(clean_name("sri RAMA RAO"), "Rama Rao")
        self.assertEqual(clean_name("Dr.  B.R. Ambedkar"), "B.R. Ambedkar")

    def test_clean_address_str(self):
        raw = "Line 1\nLine 2,\n\nLine 3"
        self.assertEqual(clean_address_str(raw), "Line 1, Line 2, Line 3")

    def test_clean_generic(self):
        self.assertEqual(clean_generic("  hello   world  "), "hello world")

if __name__ == "__main__":
    unittest.main()
