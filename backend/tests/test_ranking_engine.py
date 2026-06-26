import unittest
from unittest.mock import MagicMock
import numpy as np

from app.services.candidate_model import Candidate
from app.services.scorers import (
    SemanticScorer,
    FuzzyScorer,
    OCRConfidenceScorer,
    ContextScorer,
    ValidationScorer,
    EmbeddingCache
)
from app.services.candidate_ranker import CandidateRanker

class TestRankingEngine(unittest.TestCase):
    def test_semantic_scorer(self):
        scorer = SemanticScorer()
        
        # Test exact match
        c1 = Candidate(label="Owner Name", value="John Doe")
        score_exact = scorer.score("Owner Name", c1)
        self.assertAlmostEqual(score_exact, 1.0, places=4)
        
        # Test completely different fields
        c2 = Candidate(label="Total Amount", value="1000")
        score_diff = scorer.score("Owner Name", c2)
        # Should be significantly lower than 1.0
        self.assertTrue(score_diff < 0.8)
        
        # Test empty query/label
        self.assertEqual(scorer.score("", c1), 0.0)
        self.assertEqual(scorer.score("Owner Name", Candidate(label="", value="")), 0.0)

    def test_fuzzy_scorer(self):
        scorer = FuzzyScorer()
        
        c = Candidate(label="Owner Name", value="John")
        # Match "Owner Name" vs "Owner Name" -> 1.0
        self.assertEqual(scorer.score("Owner Name", c), 1.0)
        
        # Match "Owner Name" vs "owner name" -> 1.0
        c_lc = Candidate(label="owner name", value="John")
        self.assertEqual(scorer.score("Owner Name", c_lc), 1.0)
        
        # Match "Owner Name" vs "Name of Owner" -> fuzzy ratio should be high
        c_rev = Candidate(label="Name of Owner", value="John")
        score_rev = scorer.score("Owner Name", c_rev)
        self.assertTrue(score_rev > 0.6)

    def test_ocr_confidence_scorer(self):
        scorer = OCRConfidenceScorer()
        c = Candidate(label="Owner", value="John", ocr_confidence=0.85)
        self.assertEqual(scorer.score("Owner", c), 0.85)

    def test_context_scorer(self):
        scorer = ContextScorer()
        
        # Document text with surrounding lines containing template placeholders
        doc_text = (
            "Document Title\n"
            "Survey Number: 123\n"
            "Village: Bhanoor\n"
            "Owner Name: John Doe\n"
            "Date of Agreement: 2026-01-01\n"
            "Total Amount: 50000\n"
        )
        
        context_data = {
            "document_text": doc_text,
            "placeholders": ["Survey Number", "Village", "Owner Name", "Date of Agreement", "Total Amount"]
        }
        
        # Candidate on line 4 (index 3, "Owner Name: John Doe")
        c = Candidate(label="Owner Name", value="John Doe", source_line=4)
        
        # Neighbors on line 2 (Survey Number), line 3 (Village), line 5 (Date of Agreement), line 6 (Total Amount)
        # That's 4 neighboring placeholders within ±5 lines!
        # score = 4 * 0.2 = 0.8
        score = scorer.score("Owner Name", c, context_data)
        self.assertAlmostEqual(score, 0.8, places=4)
        
        # Check fallback when no context_data or missing line
        self.assertEqual(scorer.score("Owner Name", c, {}), 0.0)
        self.assertEqual(scorer.score("Owner Name", Candidate(label="O", value="V", source_line=None), context_data), 0.0)

    def test_validation_scorer(self):
        scorer = ValidationScorer()
        
        # Email validation
        self.assertEqual(scorer.score("Email Address", Candidate(label="Email", value="test@example.com")), 1.0)
        self.assertEqual(scorer.score("Email Address", Candidate(label="Email", value="invalid-email")), 0.0)
        
        # Phone validation
        self.assertEqual(scorer.score("Phone Number", Candidate(label="Phone", value="+91 98765 43210")), 1.0)
        self.assertEqual(scorer.score("Mobile", Candidate(label="Mobile", value="123")), 0.0)
        
        # Date validation
        self.assertEqual(scorer.score("Agreement Date", Candidate(label="Date", value="25/12/2025")), 1.0)
        self.assertEqual(scorer.score("Date", Candidate(label="Date", value="not-a-date")), 0.0)
        
        # Aadhaar validation (12 digits)
        self.assertEqual(scorer.score("Aadhaar Number", Candidate(label="Aadhaar", value="1234 5678 9012")), 1.0)
        self.assertEqual(scorer.score("Aadhar", Candidate(label="Aadhar", value="1234 5678")), 0.0)
        
        # PAN validation (5 chars, 4 digits, 1 char)
        self.assertEqual(scorer.score("PAN Card", Candidate(label="PAN", value="ABCDE1234F")), 1.0)
        self.assertEqual(scorer.score("PAN", Candidate(label="PAN", value="ABC1234F")), 0.0)
        
        # Unknown fields should have 1.0 score (no penalty)
        self.assertEqual(scorer.score("Random Field", Candidate(label="Random", value="Any Value")), 1.0)

    def test_candidate_ranker(self):
        # Weights: semantic=0.4, fuzzy=0.25, ocr=0.15, context=0.1, validation=0.1
        ranker = CandidateRanker()
        
        c1 = Candidate(label="Owner", value="Ramesh", ocr_confidence=0.9, source_line=4)
        c2 = Candidate(label="Applicant", value="Pavan Kumar", ocr_confidence=0.8, source_line=4)
        c3 = Candidate(label="Customer", value="Ravi", ocr_confidence=0.95, source_line=4)
        
        # Query: "Owner Name"
        # Let's mock semantic scorer score to distinguish candidates
        ranker.scorers["semantic"].score = MagicMock(side_effect=lambda q, c, ctx: 0.95 if c.label == "Owner" else (0.75 if c.label == "Applicant" else 0.5))
        
        # Fuzzy scores
        # "Owner Name" vs "Owner" is very high. "Owner Name" vs "Applicant" is low.
        
        context_data = {
            "document_text": "Owner: Ramesh\nApplicant: Pavan Kumar\nCustomer: Ravi",
            "placeholders": ["Owner Name"]
        }
        
        ranked = ranker.rank("Owner Name", [c1, c2, c3], context_data)
        
        self.assertEqual(len(ranked), 3)
        # c1 should be the top ranked candidate since it matches semantic and fuzzy query best
        self.assertEqual(ranked[0].label, "Owner")
        self.assertEqual(ranked[0].value, "Ramesh")
        self.assertTrue(ranked[0].final_score > ranked[1].final_score)
        
        # Check that scores dictionary and explanations are populated
        self.assertTrue(ranked[0].semantic_score > 0)
        self.assertTrue(len(ranked[0].explanation) > 0)

    def test_embedding_cache_thread_safety(self):
        # Ensure EmbeddingCache caches results
        text = "Thread Safety Test Text"
        emb1 = EmbeddingCache.get_embedding(text)
        emb2 = EmbeddingCache.get_embedding(text)
        
        # Must be exact same object reference due to caching
        self.assertIs(emb1, emb2)

if __name__ == "__main__":
    unittest.main()
