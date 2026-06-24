import unittest
from app.services.documents import rule_based_fallback_fields

class TestTableExtraction(unittest.TestCase):
    def test_table_extraction(self):
        fields = {
            "pan_number": {"value": None, "final_confidence": 0.0}
        }
        text = (
            "| Field | Value |\n"
            "| --- | --- |\n"
            "| PAN No | ABCDE1234F |\n"
        )
        required_fields = ["pan_number"]
        res = rule_based_fallback_fields(fields, text, required_fields)
        self.assertIsNotNone(res["pan_number"]["value"])
        self.assertEqual(res["pan_number"]["value"], "ABCDE1234F")
        self.assertEqual(res["pan_number"]["match_type"], "table")

if __name__ == "__main__":
    unittest.main()
