import unittest
from app.services.documents import rule_based_fallback_fields

class TestFuzzyMatching(unittest.TestCase):
    def test_fuzzy_label_match(self):
        fields = {
            "pan_number": {"value": None, "final_confidence": 0.0}
        }
        # "PAN Number" is in the aliases of "pan_number".
        # We write "PAM Numbir - XYZ" to trigger fuzzy matching.
        text = "PAM Numbir - XYZ"
        required_fields = ["pan_number"]
        res = rule_based_fallback_fields(fields, text, required_fields)
        self.assertIsNotNone(res["pan_number"]["value"])
        self.assertEqual(res["pan_number"]["value"], "XYZ")
        self.assertEqual(res["pan_number"]["match_type"], "fuzzy")

if __name__ == "__main__":
    unittest.main()
