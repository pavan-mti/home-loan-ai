from typing import Any, Dict, List
from .candidate_model import Candidate
from .scorers import (
    SemanticScorer,
    FuzzyScorer,
    OCRConfidenceScorer,
    ContextScorer,
    ValidationScorer
)

class CandidateRanker:
    def __init__(self, weights: Dict[str, float] = None):
        if weights is None:
            self.weights = {
                "semantic": 0.4,
                "fuzzy": 0.25,
                "ocr": 0.15,
                "context": 0.1,
                "validation": 0.1
            }
        else:
            self.weights = weights

        self.scorers = {
            "semantic": SemanticScorer(),
            "fuzzy": FuzzyScorer(),
            "ocr": OCRConfidenceScorer(),
            "context": ContextScorer(),
            "validation": ValidationScorer()
        }

    def rank(self, query: str, candidates: List[Candidate], context_data: Dict[str, Any] = None) -> List[Candidate]:
        if not candidates:
            return []

        for candidate in candidates:
            # Score candidate with each scorer
            candidate.semantic_score = self.scorers["semantic"].score(query, candidate, context_data)
            candidate.fuzzy_score = self.scorers["fuzzy"].score(query, candidate, context_data)
            candidate.ocr_confidence = float(candidate.ocr_confidence or 0.0)
            candidate.context_score = self.scorers["context"].score(query, candidate, context_data)
            candidate.validation_score = self.scorers["validation"].score(query, candidate, context_data)

            # OCR score is from candidate.ocr_confidence
            ocr_score = self.scorers["ocr"].score(query, candidate, context_data)

            # Compute final weighted score
            final_score = (
                self.weights.get("semantic", 0.4) * candidate.semantic_score +
                self.weights.get("fuzzy", 0.25) * candidate.fuzzy_score +
                self.weights.get("ocr", 0.15) * ocr_score +
                self.weights.get("context", 0.1) * candidate.context_score +
                self.weights.get("validation", 0.1) * candidate.validation_score
            )

            # Ensure final score is a float
            candidate.final_score = float(final_score)

            # Construct explanation
            explanation_parts = [
                f"semantic={candidate.semantic_score:.2f} (wt={self.weights.get('semantic', 0.4):.2f})",
                f"fuzzy={candidate.fuzzy_score:.2f} (wt={self.weights.get('fuzzy', 0.25):.2f})",
                f"ocr={ocr_score:.2f} (wt={self.weights.get('ocr', 0.15):.2f})",
                f"context={candidate.context_score:.2f} (wt={self.weights.get('context', 0.1):.2f})",
                f"validation={candidate.validation_score:.2f} (wt={self.weights.get('validation', 0.1):.2f})"
            ]
            candidate.explanation = f"Final Score: {candidate.final_score:.3f} | " + " | ".join(explanation_parts)

        # Sort descending by final_score, breaking ties with ocr_confidence/fuzzy/semantic
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (c.final_score, c.ocr_confidence, c.fuzzy_score, c.semantic_score),
            reverse=True
        )

        return sorted_candidates
