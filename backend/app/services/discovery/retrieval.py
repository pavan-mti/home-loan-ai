from __future__ import annotations
import re
from ..candidate_model import Candidate
from .repository import CandidateRepository

WEAK_TOKENS = {"name", "number", "area", "address", "no", "date", "id", "code", "details", "information", "value", "s", "es"}

STRONG_TOKENS = {
    "owner", "survey", "village", "industrial", "residential", "applicant", "purchaser",
    "door", "plot", "ward", "taluka", "mandal", "district", "city", "town", "layout",
    "authority", "prohibited", "opinion", "inspection", "valuation", "buyer", "seller",
    "vendor", "vendee", "builder", "developer", "agreement", "deed", "permit", "permission",
    "mortgage", "extent", "built", "plinth", "carpet", "land", "tenure"
}

NEGATIVE_INDICATORS = {
    "door": ["ltd", "pvt", "company", "bank", "synergy", "synergy pvt", "corporation"],
    "plot": ["ltd", "pvt", "company", "bank"],
    "survey": ["ltd", "pvt", "company", "bank"],
    "owner": ["ltd", "pvt", "bank"],
    "purchaser": ["ltd", "pvt", "bank"]
}

def is_false_semantic_positive(query: str, label: str) -> bool:
    q_words = {w.lower() for w in re.split(r"\s+", query) if w.strip()}
    l_words = {w.lower() for w in re.split(r"\s+", label) if w.strip()}
    
    q_specific = q_words - WEAK_TOKENS
    l_specific = l_words - WEAK_TOKENS
    
    if q_specific and l_specific:
        if q_specific & l_specific:
            return False
            
        for qw in q_specific:
            for lw in l_specific:
                if qw in lw or lw in qw:
                    return False
                    
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
                
        return True
        
    return False

def has_negative_indicator(placeholder: str, candidate: Candidate) -> bool:
    ph_lc = placeholder.lower()
    val_lc = candidate.value.lower()
    
    for key_term, negatives in NEGATIVE_INDICATORS.items():
        if key_term in ph_lc:
            for neg in negatives:
                if re.search(rf"\b{re.escape(neg)}\b", val_lc):
                    return True
    return False

class CandidateRetrieval:
    def __init__(self, semantic_threshold: float = 0.75, fuzzy_threshold: float = 0.6):
        self.semantic_threshold = semantic_threshold
        self.fuzzy_threshold = fuzzy_threshold

    def retrieve(self, placeholder: str, repository: CandidateRepository) -> list[Candidate]:
        if not placeholder or not repository.get_all():
            return []

        placeholder_lc = placeholder.strip().lower()
        ph_words = {w for w in re.split(r"\W+", placeholder_lc) if w}
        ph_strong = ph_words & STRONG_TOKENS

        retrieved = []

        from ..scorers import SemanticScorer, FuzzyScorer
        semantic_scorer = SemanticScorer()
        fuzzy_scorer = FuzzyScorer()

        for candidate in repository.get_all():
            # Apply negative indicator check
            if has_negative_indicator(placeholder, candidate):
                continue

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

            # Strong Token Overlap Gate
            cand_words = {w for w in re.split(r"\W+", cand_label_lc) if w}
            cand_strong = cand_words & STRONG_TOKENS
            if ph_strong and cand_strong and not (ph_strong & cand_strong):
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
