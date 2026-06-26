import unittest
from unittest.mock import MagicMock
from app.services.candidate_model import Candidate
from app.services.discovery.index import DocumentIndex
from app.services.discovery.repository import CandidateRepository
from app.services.discovery.retrieval import CandidateRetrieval
from app.services.discovery.engine import CandidateDiscoveryEngine

from app.services.discovery.key_value import KeyValueDiscoveryStrategy
from app.services.discovery.table import TableDiscoveryStrategy
from app.services.discovery.section import SectionDiscoveryStrategy
from app.services.discovery.nearby_label import NearbyLabelDiscoveryStrategy
from app.services.discovery.paragraph import ParagraphDiscoveryStrategy

class TestDiscoveryEngine(unittest.TestCase):
    def setUp(self):
        self.doc_text = (
            "AGREEMENT OF SALE\n\n"
            "This Agreement is dated 24-06-2026.\n"
            "Owner Name : John Doe\n"
            "Village: Bhanoor\n\n"
            "PROPERTY DETAILS\n"
            "Survey Number: 123/A\n"
            "Extent: 500 Sq Yds\n\n"
            "SCHEDULE OF PROPERTY\n"
            "| Item | Value |\n"
            "| --- | --- |\n"
            "| Pincode | 502300 |\n"
            "| District | Sangareddy |\n\n"
            "The property belongs to Mr. Ramesh Kumar residing at Hyderabad.\n"
            "Electric Meter Number EM-999 is installed in the premises.\n"
        )
        self.context = DocumentIndex(self.doc_text)

    def test_document_index_parsing(self):
        # Lines check
        self.assertTrue(len(self.context.lines) > 10)
        
        # Sections check
        sections = self.context.sections
        headings = [sec["heading"] for sec in sections]
        self.assertIn("PROPERTY DETAILS", headings)
        self.assertIn("SCHEDULE OF PROPERTY", headings)
        
        # Key values check
        kvs = self.context.key_values
        labels = [kv["label"] for kv in kvs]
        self.assertIn("Owner Name", labels)
        self.assertIn("Survey Number", labels)
        
        # Tables check
        tables = self.context.tables
        self.assertEqual(len(tables), 1)
        self.assertIn("Pincode", tables[0][1]["parts"])

    def test_key_value_discovery_strategy(self):
        strategy = KeyValueDiscoveryStrategy()
        candidates = strategy.discover(self.context)
        
        # Should discover Owner Name and Survey Number
        labels = [c.label for c in candidates]
        values = [c.value for c in candidates]
        
        self.assertIn("Owner Name", labels)
        self.assertIn("John Doe", values)
        self.assertIn("Survey Number", labels)
        self.assertIn("123/A", values)

    def test_table_discovery_strategy(self):
        strategy = TableDiscoveryStrategy()
        candidates = strategy.discover(self.context)
        
        labels = [c.label for c in candidates]
        values = [c.value for c in candidates]
        
        # Vertical / column header check or cell-pairing check
        self.assertIn("Pincode", labels)
        self.assertIn("502300", values)

    def test_section_discovery_strategy(self):
        strategy = SectionDiscoveryStrategy()
        candidates = strategy.discover(self.context)
        
        # Should produce candidates where section heading is label
        labels = [c.label for c in candidates]
        self.assertIn("PROPERTY DETAILS", labels)
        self.assertIn("SCHEDULE OF PROPERTY", labels)

    def test_nearby_label_discovery_strategy(self):
        strategy = NearbyLabelDiscoveryStrategy()
        candidates = strategy.discover(self.context)
        
        # Should capture Electric Meter Number EM-999 (Title case prefix + value space split)
        labels = [c.label for c in candidates]
        values = [c.value for c in candidates]
        self.assertIn("Electric Meter Number", labels)
        self.assertIn("EM-999 is installed in the premises.", values)

    def test_paragraph_discovery_strategy(self):
        strategy = ParagraphDiscoveryStrategy()
        candidates = strategy.discover(self.context)
        
        # Relational splitter: "belongs to Mr. Ramesh Kumar..." -> "belongs to"
        # value: "Mr" or "Ramesh Kumar" (splitting on punctuation)
        labels = [c.label for c in candidates]
        values = [c.value for c in candidates]
        
        self.assertIn("property belongs to", labels)
        self.assertIn("Mr. Ramesh Kumar residing at Hyderabad", values)

    def test_candidate_retrieval(self):
        # Create a repo with some candidates
        c1 = Candidate(label="Owner Name", value="John Doe", ocr_confidence=0.9)
        c2 = Candidate(label="Applicant", value="Ramesh", ocr_confidence=0.8)
        c3 = Candidate(label="District", value="Sangareddy", ocr_confidence=0.9)
        
        repo = CandidateRepository([c1, c2, c3])
        retrieval = CandidateRetrieval()
        
        # 1. Exact match
        res_exact = retrieval.retrieve("Owner Name", repo)
        self.assertEqual(len(res_exact), 1)
        self.assertEqual(res_exact[0].value, "John Doe")
        
        # 2. Normalized match
        res_norm = retrieval.retrieve("owner name", repo)
        self.assertEqual(len(res_norm), 1)
        self.assertEqual(res_norm[0].value, "John Doe")
        
        # 3. Fuzzy match
        res_fuzzy = retrieval.retrieve("District Name", repo)
        self.assertEqual(len(res_fuzzy), 1)
        self.assertEqual(res_fuzzy[0].value, "Sangareddy")
        
        # 4. Semantic match
        # Mock SemanticScorer to match "Owner Name" with "Applicant"
        with unittest.mock.patch('app.services.scorers.SemanticScorer.score', return_value=0.95):
            res_sem = retrieval.retrieve("Owner Name", repo)
            labels = [c.label for c in res_sem]
            self.assertIn("Applicant", labels)

    def test_engine_merging_and_filtering(self):
        engine = CandidateDiscoveryEngine()
        
        # Test validation filters (quality check)
        c_valid = Candidate(label="Name", value="John", ocr_confidence=0.9)
        c_empty = Candidate(label="Name", value="", ocr_confidence=0.8)
        c_short = Candidate(label="Name", value="A", ocr_confidence=0.8)  # short non-digit
        c_short_digit = Candidate(label="Age", value="5", ocr_confidence=0.8) # short digit
        c_punct = Candidate(label="Name", value="---", ocr_confidence=0.8)
        
        self.assertTrue(engine._is_valid_candidate(c_valid))
        self.assertFalse(engine._is_valid_candidate(c_empty))
        self.assertFalse(engine._is_valid_candidate(c_short))
        self.assertTrue(engine._is_valid_candidate(c_short_digit))
        self.assertFalse(engine._is_valid_candidate(c_punct))
        
        # Test merging duplicates
        c1 = Candidate(label="Owner Name", value="John", ocr_confidence=0.8, discovery_strategy="key_value")
        c2 = Candidate(label="owner name", value="john", ocr_confidence=0.95, discovery_strategy="nearby_label")
        
        merged = engine._merge_duplicates([c1, c2])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].ocr_confidence, 0.95)
        self.assertIn("key_value", merged[0].discovery_strategy)
        self.assertIn("nearby_label", merged[0].discovery_strategy)

    def test_document_scanned_once(self):
        # We can verify that DocumentIndex properties cache their values
        # doc_index.key_values should build once
        idx = DocumentIndex(self.doc_text)
        
        # Mock builder method
        idx._build_key_values = MagicMock(return_value=[])
        
        # Access property twice
        k1 = idx.key_values
        k2 = idx.key_values
        
        idx._build_key_values.assert_called_once()

if __name__ == "__main__":
    unittest.main()
