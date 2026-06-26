from __future__ import annotations
import re
from ..candidate_model import Candidate
from .repository import CandidateRepository

def is_false_semantic_positive(query: str, label: str) -> bool:
    q_words = {w.lower() for w in re.split(r"\s+", query) if w.strip()}
    l_words = {w.lower() for w in re.split(r"\s+", label) if w.strip()}
    
    # Generic suffix words
    generic = {"number", "no", "id", "code", "name", "date", "details", "information", "value"}
    
    # Non-generic words (specific words)
    q_specific = q_words - generic
    l_specific = l_words - generic
    
    # If both have specific words, but they share NO words and no word is a substring,
    # then it's highly likely to be a false semantic match unless they are synonyms.
    if q_specific and l_specific:
        # Check for exact intersection
        if q_specific & l_specific:
            return False
            
        # Check for substring overlap (e.g. "meter" in "electric_meter")
        for qw in q_specific:
            for lw in l_specific:
                if qw in lw or lw in qw:
                    return False
                    
        # Check for known synonym pairs
        synonyms = [
            {"owner", "applicant", "borrower", "proprietor", "landlord", "lessor"},
            {"purchaser", "buyer", "vendee"},
            {"vendor", "seller"},
            {"tenant", "lessee", "occupant"},
            {"amount", "price", "cost", "value", "consideration", "premium", "rs", "rupees"},
            {"date", "day", "month", "year"},
            {"address", "location", "premises", "property"}
        ]
        for syn_set in synonyms:
            if any(qw in syn_set for qw in q_specific) and any(lw in syn_set for lw in l_specific):
                return False
                
        return True # It is a false positive
        
    return False

class CandidateRetrieval:
    def __init__(self, semantic_threshold: float = 0.75, fuzzy_threshold: float = 0.6):
        self.semantic_threshold = semantic_threshold
        self.fuzzy_threshold = fuzzy_threshold

    def retrieve(self, placeholder: str, repository: CandidateRepository) -> list[Candidate]:
        if not placeholder or not repository.get_all():
            return []

        placeholder_lc = placeholder.strip().lower()
        retrieved = []

        from ..scorers import SemanticScorer, FuzzyScorer
        semantic_scorer = SemanticScorer()
        fuzzy_scorer = FuzzyScorer()

        for candidate in repository.get_all():
            # Exact Match
            if candidate.label == placeholder:
                retrieved.append(candidate)
                continue

            # Normalized Match
            cand_label_lc = candidate.label.strip().lower()
            if cand_label_lc == placeholder_lc:
                retrieved.append(candidate)
                continue

            # Check if it is a false positive
            if is_false_semantic_positive(placeholder, candidate.label):
                continue

            # Fuzzy Match
            f_score = fuzzy_scorer.score(placeholder, candidate)
            if f_score >= self.fuzzy_threshold:
                retrieved.append(candidate)
                continue

            # Semantic Match
            s_score = semantic_scorer.score(placeholder, candidate)
            if s_score >= self.semantic_threshold:
                retrieved.append(candidate)
                continue

        # De-duplicate retrieved list
        unique_retrieved = []
        seen_ids = set()
        for c in retrieved:
            c_id = id(c)
            if c_id not in seen_ids:
                seen_ids.add(c_id)
                unique_retrieved.append(c)

        return unique_retrieved
