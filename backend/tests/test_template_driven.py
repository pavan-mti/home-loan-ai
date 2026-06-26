import unittest
from app.services.documents import analyze_document

class TestTemplateDriven(unittest.TestCase):
    def test_custom_placeholders(self):
        text = "Electric Meter Number: EM1234567\nTransformer ID - TR-999"
        placeholders = ["Electric Meter Number", "Transformer ID", "Owner Name"]
        
        # Test that analyze_document attempts extraction for all placeholders,
        # including custom ones that do not exist in MASTER_DICTIONARY.
        results = analyze_document(text, placeholders)
        
        extracted_dict = {item["field_name"]: item["value"] for item in results}
        
        self.assertEqual(extracted_dict.get("Electric Meter Number"), "EM1234567")
        self.assertEqual(extracted_dict.get("Transformer ID"), "TR-999")
        self.assertIsNone(extracted_dict.get("Owner Name"))

    def test_placeholder_extractor_strategies(self):
        from app.services.placeholder_extractor import (
            extract_placeholder,
            strategy_exact,
            strategy_normalized,
            strategy_table,
            aggregate_and_rank_candidates
        )
        
        # 1. Test Exact Strategy
        lines = ["Owner Name: John Doe", "owner name: Jane Doe"]
        exact_cands = strategy_exact("Owner Name", ["Owner Name"], lines)
        self.assertEqual(len(exact_cands), 1)
        self.assertEqual(exact_cands[0]["value"], "John Doe")
        self.assertEqual(exact_cands[0]["strategy"], "Exact")
        
        # 2. Test Normalized Strategy
        norm_cands = strategy_normalized("Owner Name", ["Owner Name"], lines)
        self.assertEqual(len(norm_cands), 2)
        self.assertEqual(norm_cands[0]["value"], "John Doe")
        self.assertEqual(norm_cands[1]["value"], "Jane Doe")
        
        # 3. Test aggregate_and_rank_candidates
        all_cands = exact_cands + norm_cands
        best = aggregate_and_rank_candidates(all_cands)
        self.assertEqual(best["strategy"], "Exact")
        self.assertEqual(best["value"], "John Doe")
        
        # 4. Test Table Strategy
        table_lines = ["Owner Name | John Doe"]
        table_cands = strategy_table("Owner Name", ["Owner Name"], table_lines)
        self.assertEqual(len(table_cands), 1)
        self.assertEqual(table_cands[0]["value"], "John Doe")
        
        # 5. Test extract_placeholder end-to-end
        doc = "Some unrelated text\nElectric Meter Number: EM-999\nAnother text"
        res = extract_placeholder("Electric Meter Number", doc)
        self.assertEqual(res["value"], "EM-999")
        self.assertEqual(res["strategy"], "Exact")

    def test_milestone_3_1_validation_checklist(self):
        # Test Case 1 — Existing Field
        text_1 = "Owner Name: Pavan Kumar"
        res_1 = analyze_document(text_1, ["Owner Name"])
        extracted_dict_1 = {item["field_name"]: item["value"] for item in res_1}
        self.assertEqual(extracted_dict_1.get("Owner Name"), "Pavan Kumar")

        # Test Case 2 — Unknown Placeholder
        text_2 = "Electric Meter Number : 987654321"
        res_2 = analyze_document(text_2, ["Electric Meter Number"])
        extracted_dict_2 = {item["field_name"]: item["value"] for item in res_2}
        self.assertEqual(extracted_dict_2.get("Electric Meter Number"), "987654321")

        # Test Case 3 — Multiple Unknown Fields
        text_3 = (
            "Factory License Number : FL-9921\n\n"
            "Transformer Number : TR-123\n\n"
            "Consumer ID : C998812"
        )
        placeholders_3 = ["Factory License Number", "Transformer Number", "Consumer ID"]
        res_3 = analyze_document(text_3, placeholders_3)
        extracted_dict_3 = {item["field_name"]: item["value"] for item in res_3}
        self.assertEqual(extracted_dict_3.get("Factory License Number"), "FL-9921")
        self.assertEqual(extracted_dict_3.get("Transformer Number"), "TR-123")
        self.assertEqual(extracted_dict_3.get("Consumer ID"), "C998812")

        # Test Case 4 — Mixed Template
        text_4 = "Owner Name: Pavan Kumar\nElectric Meter Number: 123456"
        placeholders_4 = ["Owner Name", "Survey Number", "Electric Meter Number", "GST Number", "Village"]
        res_4 = analyze_document(text_4, placeholders_4)
        extracted_dict_4 = {item["field_name"]: item["value"] for item in res_4}
        self.assertEqual(extracted_dict_4.get("Owner Name"), "Pavan Kumar")
        self.assertEqual(extracted_dict_4.get("Electric Meter Number"), "123456")
        self.assertIsNone(extracted_dict_4.get("Survey Number"))
        self.assertIsNone(extracted_dict_4.get("GST Number"))
        self.assertIsNone(extracted_dict_4.get("Village"))

        # Failure Handling Check
        # If no value can be extracted, must return: value=None, confidence=0, validation_message="No matching candidate found"
        missing_item = next(item for item in res_4 if item["field_name"] == "GST Number")
        self.assertIsNone(missing_item["value"])
        self.assertEqual(missing_item["confidence"], 0)
        self.assertEqual(missing_item["reason"], "No matching candidate found")
        self.assertEqual(missing_item["validation_message"], "No matching candidate found")

if __name__ == "__main__":
    unittest.main()
