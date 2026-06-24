import unittest
from app.services.documents import rule_based_fallback_fields

class TestRegexFields(unittest.TestCase):
    def test_regex_fallback(self):
        fields = {
            "inspection_date": {"value": None, "final_confidence": 0.0}
        }
        text = "Inspection Date: 17/02/2026"
        required_fields = ["inspection_date"]
        res = rule_based_fallback_fields(fields, text, required_fields)
        self.assertIsNotNone(res["inspection_date"]["value"])
        self.assertEqual(res["inspection_date"]["value"], "17/02/2026")
        self.assertEqual(res["inspection_date"]["match_type"], "same_line") # it'll match same_line, which is higher priority and also cleaned

    def test_regex_pure_fallback(self):
        fields = {
            "inspection_date": {"value": None, "final_confidence": 0.0}
        }
        # In this text, we don't have the label, just a date pattern on a line.
        # But wait, regex fallback matches if the field_code is in the line or via extract_regex_value.
        # Let's test with a line containing the code/label and date pattern.
        text = "some text inspection_date some other 24-06-2026 text"
        required_fields = ["inspection_date"]
        res = rule_based_fallback_fields(fields, text, required_fields)
        self.assertIsNotNone(res["inspection_date"]["value"])
        self.assertEqual(res["inspection_date"]["value"], "24-06-2026")
        self.assertEqual(res["inspection_date"]["match_type"], "regex")

if __name__ == "__main__":
    unittest.main()
