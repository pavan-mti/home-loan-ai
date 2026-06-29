from __future__ import annotations

import os
import re
from typing import Any
from .gemini_service import GeminiService
from .candidate_model import Candidate
from .candidate_ranker import CandidateRanker
from .discovery.repository import CandidateRepository

MIN_ACCEPTABLE_SCORE = float(os.getenv("MIN_ACCEPTABLE_SCORE", "0.65"))

def strategy_exact(placeholder: str, search_labels: list[str], lines: list[str]) -> list[dict[str, Any]]:
    candidates = []
    for label in search_labels:
        pattern_exact = rf"\b{re.escape(label)}\b\s*[:\-–—=]?\s*(.+)"
        for idx, line in enumerate(lines):
            match = re.search(pattern_exact, line)
            if match:
                val = match.group(1).strip()
                if val and len(val) >= 2 and len(val) < 200:
                    candidates.append({
                        "value": val,
                        "confidence": 0.95,
                        "strategy": "Exact",
                        "matched_label": label,
                        "source_line": idx + 1
                    })
    return candidates

def strategy_normalized(placeholder: str, search_labels: list[str], lines: list[str]) -> list[dict[str, Any]]:
    candidates = []
    for label in search_labels:
        pattern_norm = rf"(?i)\b{re.escape(label)}\b\s*[:\-–—=]?\s*(.+)"
        for idx, line in enumerate(lines):
            match = re.search(pattern_norm, line)
            if match:
                val = match.group(1).strip()
                if val and len(val) >= 2 and len(val) < 200:
                    candidates.append({
                        "value": val,
                        "confidence": 0.92,
                        "strategy": "Normalized",
                        "matched_label": label,
                        "source_line": idx + 1
                    })
    return candidates

def strategy_table(placeholder: str, search_labels: list[str], lines: list[str]) -> list[dict[str, Any]]:
    candidates = []
    for label in search_labels:
        pattern_table = rf"(?i)\b{re.escape(label)}\b"
        for line_idx, line in enumerate(lines):
            if re.search(pattern_table, line) and ("|" in line or "  " in line):
                parts = [p.strip() for p in re.split(r"\||\s{2,}", line) if p.strip()]
                if len(parts) > 1:
                    for p_idx, part in enumerate(parts):
                        if re.search(pattern_table, part):
                            if p_idx + 1 < len(parts):
                                val = parts[p_idx + 1]
                                candidates.append({
                                    "value": val,
                                    "confidence": 0.90,
                                    "strategy": "Table",
                                    "matched_label": label,
                                    "source_line": line_idx + 1
                                })
    return candidates

def strategy_regex(placeholder: str, document_text: str) -> list[dict[str, Any]]:
    candidates = []
    placeholder_lc = placeholder.lower()
    if "permit" in placeholder_lc or "permission" in placeholder_lc:
        regex_patterns = [
            r"PERMIT\s*NO\.?\s*[:\s-]*\s*([A-Z0-9/\-_.()]{4,})",
            r"FILE\s*NO\.?\s*[:\s-]*\s*([A-Z0-9/\-_.()]{4,})",
            r"BUILDING\s*PERMISSION\s*NUMBER\s*[:\s-]*\s*([A-Z0-9/\-_.()]{4,})",
        ]
    elif "rera" in placeholder_lc:
        regex_patterns = [
            r"RERA\s*(?:REGISTRATION|REG|NO)?\.?\s*[:\s-]*\s*([A-Z0-9/\-_.()]{4,})",
            r"RERA.*?([A-Z0-9/\-_.()]{4,})",
        ]
    elif "survey" in placeholder_lc:
        regex_patterns = [
            r"SURVEY\s*NO\.?\s*[:\-]?\s*([A-Za-z0-9/\-,\s()]+)",
            r"SY\.?\s*NO\.?\s*[:\-]?\s*([A-Za-z0-9/\-,\s()]+)",
        ]
    elif "plot" in placeholder_lc:
        regex_patterns = [
            r"PLOT\s*NO\.?\s*[:\-]?\s*([A-Za-z0-9/\-,\s()]+)",
        ]
    elif "flat" in placeholder_lc:
        regex_patterns = [
            r"FLAT\s*NO\.?\s*[:\-]?\s*([A-Za-z0-9/\-,\s()]+)",
        ]
    else:
        regex_patterns = []

    for pat in regex_patterns:
        match = re.search(pat, document_text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            val = match.group(1).strip()
            val = re.sub(r"^[ :\-=]+", "", val).strip("., ")
            if val and len(val) >= 2:
                if "survey" in placeholder_lc or "plot" in placeholder_lc or "flat" in placeholder_lc:
                    val = val.split("\n")[0].strip()
                candidates.append({
                    "value": val,
                    "confidence": 0.90,
                    "strategy": "Regex",
                    "matched_label": placeholder,
                    "source_line": None
                })
    return candidates

def _get_relevant_chunks(text: str, keywords: list[str], label: str) -> str:
    if not text:
        return ""

    terms = list(keywords)
    if label:
        terms.append(label)

    lines = text.split("\n")
    matching_lines: list[int] = []
    for i, line in enumerate(lines):
        if any(re.search(re.escape(term), line, flags=re.IGNORECASE) for term in terms if term.strip()):
            matching_lines.append(i)

    if not matching_lines:
        return "\n".join(lines[:100])

    selected_indices: set[int] = set()
    for idx in matching_lines:
        start = max(0, idx - 15)
        end = min(len(lines), idx + 15)
        for j in range(start, end):
            selected_indices.add(j)

    sorted_indices = sorted(list(selected_indices))

    chunks: list[str] = []
    last_idx = -2
    for idx in sorted_indices:
        if idx > last_idx + 1:
            chunks.append("... [gap] ...")
        chunks.append(lines[idx])
        last_idx = idx

    chunk_text = "\n".join(chunks)
    return chunk_text[:8000]

def strategy_context(placeholder: str, search_labels: list[str], lines: list[str], document_text: str, gemini_service: GeminiService | None = None) -> list[dict[str, Any]]:
    candidates = []
    placeholder_lc = placeholder.lower()
    
    # 1. Nearby / Next-Line / Multi-line Value Search
    for label in search_labels:
        pattern_label_only = rf"(?i)\b{re.escape(label)}\b"
        for idx, line in enumerate(lines):
            if re.search(pattern_label_only, line):
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1].strip()
                    if next_line and len(next_line) >= 2 and ":" not in next_line and len(next_line) < 200:
                        multiline_val = [next_line]
                        for offset in range(2, 5):
                            if idx + offset < len(lines):
                                sub_line = lines[idx + offset].strip()
                                if sub_line and len(sub_line) >= 2 and ":" not in sub_line and not any(sep in sub_line for sep in ["---", "===", "___"]):
                                    multiline_val.append(sub_line)
                                else:
                                    break
                        combined_val = "\n".join(multiline_val)
                        final_val = combined_val if len(multiline_val) > 1 else next_line
                        candidates.append({
                            "value": final_val,
                            "confidence": 0.85,
                            "strategy": "Context",
                            "matched_label": label,
                            "source_line": idx + 2
                        })

    # 2. LLM Fallback (if no candidates and service is available)
    if not candidates and gemini_service:
        text_chunk = _get_relevant_chunks(document_text, search_labels, placeholder)
        if text_chunk:
            field_code = re.sub(r"[^a-z0-9]+", "_", placeholder_lc).strip("_")
            ai_res = gemini_service.extract_field_with_llm(
                field_code=field_code,
                label=placeholder,
                keywords=search_labels,
                text_chunk=text_chunk,
            )
            if ai_res and ai_res.get("value"):
                candidates.append({
                    "value": ai_res["value"],
                    "confidence": ai_res.get("confidence", 0.85),
                    "strategy": "Context",
                    "matched_label": placeholder,
                    "source_line": None
                })
    return candidates

def aggregate_and_rank_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None

    strategy_priority = {
        "Exact": 5,
        "Normalized": 4,
        "Table": 3,
        "Regex": 2,
        "Context": 1
    }

    def sort_key(cand):
        conf = cand.get("confidence", 0.0)
        strat = cand.get("strategy", "")
        priority = strategy_priority.get(strat, 0)
        return (conf, priority)

    sorted_candidates = sorted(candidates, key=sort_key, reverse=True)
    return sorted_candidates[0]

def get_compatibility_strategy(candidate: Candidate, query: str) -> str:
    ds = (candidate.discovery_strategy or "").lower()
    if "regex" in ds:
        return "Regex"
    elif "table" in ds:
        return "Table"
    elif "context" in ds or "llm" in ds:
        return "Context"
    elif "key_value" in ds or "nearby_label" in ds:
        if candidate.label == query:
            return "Exact"
        elif candidate.label.lower() == query.lower():
            return "Normalized"
        else:
            return "Normalized"
    return "Normalized"

def extract_placeholder(
    placeholder: str, 
    document_text: str, 
    gemini_service: GeminiService | None = None,
    context_data: dict[str, Any] | None = None,
    candidate_repo: CandidateRepository | None = None
) -> dict[str, Any]:
    """
    Introduce a placeholder extraction pipeline that processes one placeholder independently of any canonical field.
    """
    if not document_text or not placeholder or not placeholder.strip():
        return {
            "value": None,
            "label": None,
            "confidence": 0.0,
            "needs_review": True,
            "strategy": None,
            "matched_label": None,
            "source_line": None,
            "reason": "No matching candidate found",
            "scores": {
                "semantic": 0.0,
                "fuzzy": 0.0,
                "context": 0.0,
                "validation": 0.0,
                "ocr": 0.0
            },
            "explanation": "Empty query or document",
            "ranked_candidates": [],
            "metadata": {}
        }

    placeholder_clean = placeholder.strip()
    placeholder_lc = placeholder_clean.lower()

    # Get optional search hints (aliases) without using canonical field names
    from .field_patterns import FIELD_LABELS_EXT
    from .extractors.base import FIELD_LABELS as BASE_LABELS

    aliases = []
    for labels_dict in (FIELD_LABELS_EXT, BASE_LABELS):
        for canon_key, label_list in labels_dict.items():
            if any(lbl.strip().lower() == placeholder_lc for lbl in label_list if lbl):
                for lbl in label_list:
                    lbl_clean = lbl.strip()
                    if lbl_clean and lbl_clean not in aliases:
                        aliases.append(lbl_clean)

    search_labels = [placeholder_clean]
    for a in aliases:
        if a not in search_labels:
            search_labels.append(a)

    # 1. Fallback to discover document once if candidate_repo not supplied
    if candidate_repo is None:
        from .discovery.index import DocumentIndex
        from .discovery.engine import CandidateDiscoveryEngine
        doc_index = DocumentIndex(document_text)
        discovery_engine = CandidateDiscoveryEngine()
        candidate_repo = discovery_engine.discover(doc_index)

    # 2. Candidate Retrieval
    from .discovery.retrieval import CandidateRetrieval
    retrieval = CandidateRetrieval()
    retrieved_candidates = retrieval.retrieve(placeholder_clean, candidate_repo)
    print("\n" + "=" * 80)
    print(f"PLACEHOLDER: {placeholder_clean}")
    print("=" * 80)

    print("\nRETRIEVED CANDIDATES:")

    if not retrieved_candidates:
        print("No candidates retrieved.")
    else:
        for i, c in enumerate(retrieved_candidates, 1):
            print(f"\nCandidate #{i}")
            print(f"  Label      : {c.label}")
            print(f"  Value      : {c.value}")
            print(f"  Strategy   : {c.discovery_strategy}")
            print(f"  OCR Conf   : {c.ocr_confidence}")
            print(f"  Page       : {c.page}")
    # 3. Add placeholder-specific Regex candidates
    regex_cands = strategy_regex(placeholder_clean, document_text)
    for rc in regex_cands:
        c_obj = Candidate(
            label=rc.get("matched_label", placeholder_clean),
            value=rc.get("value", ""),
            ocr_confidence=rc.get("confidence", 0.0),
            extraction_strategy=rc.get("strategy", ""),
            source_line=rc.get("source_line"),
            discovery_strategy="regex"
        )
        # Avoid duplicate values in retrieved list
        if not any(c.value.strip().lower() == c_obj.value.strip().lower() for c in retrieved_candidates):
            retrieved_candidates.append(c_obj)

    # 4. LLM Fallback (if no candidates retrieved)
    if not retrieved_candidates and gemini_service:
        text_chunk = _get_relevant_chunks(document_text, search_labels, placeholder_clean)
        if text_chunk:
            field_code = re.sub(r"[^a-z0-9]+", "_", placeholder_lc).strip("_")
            ai_res = gemini_service.extract_field_with_llm(
                field_code=field_code,
                label=placeholder_clean,
                keywords=search_labels,
                text_chunk=text_chunk,
            )
            if ai_res and ai_res.get("value"):
                c_obj = Candidate(
                    label=placeholder_clean,
                    value=ai_res["value"],
                    ocr_confidence=ai_res.get("confidence", 0.85),
                    extraction_strategy="Context",
                    source_line=None,
                    discovery_strategy="llm"
                )
                retrieved_candidates.append(c_obj)

    if not retrieved_candidates:
        return {
            "value": None,
            "label": None,
            "confidence": 0.0,
            "needs_review": True,
            "strategy": None,
            "matched_label": None,
            "source_line": None,
            "reason": "No matching candidate found",
            "scores": {
                "semantic": 0.0,
                "fuzzy": 0.0,
                "context": 0.0,
                "validation": 0.0,
                "ocr": 0.0
            },
            "explanation": "No candidates found",
            "ranked_candidates": [],
            "metadata": {}
        }

    # Aggregate context data
    if context_data is None:
        context_data = {
            "document_text": document_text,
            "placeholders": [placeholder_clean]
        }

    # Rank candidates using CandidateRanker
    ranker = CandidateRanker()
    ranked_objs = ranker.rank(placeholder_clean, retrieved_candidates, context_data)

    best = ranked_objs[0]

    print("\nRANKING RESULTS")

    for i, c in enumerate(ranked_objs, 1):
        print(f"\nRank #{i}")
        print(f"  Label       : {c.label}")
        print(f"  Value       : {c.value}")
        print(f"  Semantic    : {c.semantic_score:.3f}")
        print(f"  Fuzzy       : {c.fuzzy_score:.3f}")
        print(f"  Context     : {c.context_score:.3f}")
        print(f"  Validation  : {c.validation_score:.3f}")
        print(f"  OCR         : {c.ocr_confidence:.3f}")
        print(f"  Final Score : {c.final_score:.3f}")
        print("\nWINNER")
        print(f"  Label : {best.label}")
        print(f"  Value : {best.value}")
        print(f"  Score : {best.final_score:.3f}")
        print("=" * 80 + "\n")

    # Serialize ranked candidates to dicts
    ranked_candidates_serialized = []
    for c in ranked_objs:
        ranked_candidates_serialized.append({
            "label": c.label,
            "value": c.value,
            "page": c.page,
            "bounding_box": c.bounding_box,
            "ocr_confidence": c.ocr_confidence,
            "extraction_strategy": c.extraction_strategy,
            "source_line": c.source_line,
            "scores": {
                "semantic": c.semantic_score,
                "fuzzy": c.fuzzy_score,
                "context": c.context_score,
                "validation": c.validation_score,
                "ocr": c.ocr_confidence
            },
            "final_score": c.final_score,
            "explanation": c.explanation
        })

    if best.final_score < MIN_ACCEPTABLE_SCORE:
        return {
            "value": None,
            "label": None,
            "confidence": 0.0,
            "needs_review": True,
            "strategy": None,
            "matched_label": None,
            "source_line": None,
            "reason": f"Best candidate score ({best.final_score:.3f}) below threshold {MIN_ACCEPTABLE_SCORE}",
            "scores": {
                "semantic": best.semantic_score,
                "fuzzy": best.fuzzy_score,
                "context": best.context_score,
                "validation": best.validation_score,
                "ocr": best.ocr_confidence
            },
            "explanation": f"Best candidate had low score: {best.explanation}",
            "ranked_candidates": ranked_candidates_serialized,
            "metadata": {
                "all_candidates": ranked_candidates_serialized
            }
        }

    compat_strategy = get_compatibility_strategy(best, placeholder_clean)
    return {
        "value": best.value,
        "label": best.label,
        "confidence": best.final_score,
        "needs_review": best.final_score < 0.7,
        "strategy": compat_strategy,
        "matched_label": best.label,
        "source_line": best.source_line,
        "reason": None,
        "scores": {
            "semantic": best.semantic_score,
            "fuzzy": best.fuzzy_score,
            "context": best.context_score,
            "validation": best.validation_score,
            "ocr": best.ocr_confidence
        },
        "explanation": best.explanation,
        "ranked_candidates": ranked_candidates_serialized,
        "metadata": {
            "strategy": compat_strategy,
            "matched_label": best.label,
            "source_line": best.source_line,
            "all_candidates": ranked_candidates_serialized
        }
    }
