from __future__ import annotations

import re
import threading
from typing import Any
import numpy as np
from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz
from .candidate_model import Candidate

class ModelLoader:
    _model = None
    _lock = threading.Lock()

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        if cls._model is None:
            with cls._lock:
                if cls._model is None:
                    cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model

class EmbeddingCache:
    _cache: dict[str, np.ndarray] = {}
    _lock = threading.Lock()

    @classmethod
    def get_embedding(cls, text: str) -> np.ndarray:
        if not text:
            return np.zeros(384)
        
        text_clean = text.strip()
        with cls._lock:
            if text_clean in cls._cache:
                return cls._cache[text_clean]

        model = ModelLoader.get_model()
        emb = model.encode(text_clean, convert_to_numpy=True)
        
        with cls._lock:
            cls._cache[text_clean] = emb
        return emb


class BaseScorer:
    def score(self, query: str, candidate: Candidate, context_data: dict[str, Any] = None) -> float:
        raise NotImplementedError("Subclasses must implement score method")


class SemanticScorer(BaseScorer):
    def score(self, query: str, candidate: Candidate, context_data: dict[str, Any] = None) -> float:
        if not query or not candidate.label:
            return 0.0
        try:
            emb_query = EmbeddingCache.get_embedding(query)
            emb_label = EmbeddingCache.get_embedding(candidate.label)
            
            norm_query = np.linalg.norm(emb_query)
            norm_label = np.linalg.norm(emb_label)
            if norm_query == 0 or norm_label == 0:
                return 0.0
                
            similarity = np.dot(emb_query, emb_label) / (norm_query * norm_label)
            # Map cosine similarity from [-1, 1] to [0, 1]
            return float((similarity + 1.0) / 2.0)
        except Exception as e:
            print(f"Error in SemanticScorer: {e}")
            return 0.0



class FuzzyScorer(BaseScorer):
    def score(self, query: str, candidate: Candidate, context_data: dict[str, Any] = None) -> float:
        if not query or not candidate.label:
            return 0.0
        q_lc = query.lower()
        lbl_lc = candidate.label.lower()
        sort_ratio = fuzz.token_sort_ratio(q_lc, lbl_lc) / 100.0
        return float(sort_ratio)


class OCRConfidenceScorer(BaseScorer):
    def score(self, query: str, candidate: Candidate, context_data: dict[str, Any] = None) -> float:
        return float(candidate.ocr_confidence)


class ContextScorer(BaseScorer):
    def score(self, query: str, candidate: Candidate, context_data: dict[str, Any] = None) -> float:
        if not context_data:
            return 0.0
        
        doc_text = context_data.get("document_text", "")
        placeholders = context_data.get("placeholders", [])
        source_line = candidate.source_line
        
        if not doc_text or not placeholders or source_line is None:
            return 0.0
            
        lines = doc_text.splitlines()
        line_idx = source_line - 1
        
        # Extensible context slice (currently line-based ±5 lines)
        start_idx = max(0, line_idx - 5)
        end_idx = min(len(lines), line_idx + 6)
        
        context_lines = []
        for idx in range(start_idx, end_idx):
            if idx != line_idx:
                context_lines.append(lines[idx].lower())
                
        query_lc = query.lower()
        matched_placeholders = set()
        
        for p in placeholders:
            p_lc = p.lower()
            if p_lc == query_lc:
                continue
            for cline in context_lines:
                if p_lc in cline:
                    matched_placeholders.add(p_lc)
                    break
                    
        # score increases by 0.2 for each neighboring placeholder found, capped at 1.0
        score_val = len(matched_placeholders) * 0.2
        return float(min(1.0, score_val))


class ValidationScorer(BaseScorer):
    def score(self, query: str, candidate: Candidate, context_data: dict[str, Any] = None) -> float:
        val_str = candidate.value
        if not val_str:
            return 0.0
            
        query_lc = query.lower()
        
        # Email validation
        if "email" in query_lc:
            is_valid = bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', val_str.strip()))
            return 1.0 if is_valid else 0.0
            
        # Phone validation
        if any(w in query_lc for w in ["phone", "mobile", "contact"]):
            digits = re.sub(r'\D', '', val_str)
            is_valid = len(digits) >= 10 and len(digits) <= 15
            return 1.0 if is_valid else 0.0
            
        # Date validation
        if "date" in query_lc:
            is_valid = bool(re.search(r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', val_str))
            return 1.0 if is_valid else 0.0
            
        # Amount validation
        if any(w in query_lc for w in ["amount", "value", "rupee", "rs", "cost", "price"]):
            is_valid = bool(re.search(r'\d', val_str))
            return 1.0 if is_valid else 0.0
            
        # PAN validation
        if "pan" in query_lc:
            is_valid = bool(re.search(r'[A-Za-z]{5}\d{4}[A-Za-z]', val_str))
            return 1.0 if is_valid else 0.0
            
        # Aadhaar validation
        if any(w in query_lc for w in ["aadhaar", "aadhar"]):
            digits = re.sub(r'\D', '', val_str)
            is_valid = len(digits) == 12
            return 1.0 if is_valid else 0.0
            
        # Unknown placeholder types are not penalized
        return 1.0
