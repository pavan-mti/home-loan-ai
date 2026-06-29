from __future__ import annotations
from ..candidate_model import Candidate
from .index import DocumentIndex
from .repository import CandidateRepository

from .quality_gate import CandidateQualityGate
from .key_value import KeyValueDiscoveryStrategy
from .table import TableDiscoveryStrategy
from .section import SectionDiscoveryStrategy
from .nearby_label import NearbyLabelDiscoveryStrategy
from .paragraph import ParagraphDiscoveryStrategy

class CandidateDiscoveryEngine:
    def __init__(self):
        self.quality_gate = CandidateQualityGate()
        self.strategies = [
            KeyValueDiscoveryStrategy(),
            TableDiscoveryStrategy(),
            SectionDiscoveryStrategy(),
            NearbyLabelDiscoveryStrategy(),
            ParagraphDiscoveryStrategy()
        ]

    def discover(self, context: DocumentIndex) -> CandidateRepository:
        all_candidates = []
        for strategy in self.strategies:
            try:
                candidates = strategy.discover(context)
                all_candidates.extend(candidates)
            except Exception as e:
                print(f"Error in discovery strategy {strategy.__class__.__name__}: {e}")

        # Strategy 10: Apply Quality Filters
        filtered = [c for c in all_candidates if self.quality_gate.validate(c)]

        # Strategy 7: Merge duplicate candidates
        merged = self._merge_duplicates(filtered)

        return CandidateRepository(merged)

    def _is_valid_candidate(self, candidate: Candidate) -> bool:
        return self.quality_gate.validate(candidate)


    def _merge_duplicates(self, candidates: list[Candidate]) -> list[Candidate]:
        grouped = {}
        for c in candidates:
            # Group by normalized label and value
            key = (c.label.strip().lower(), c.value.strip().lower())
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(c)

        merged_list = []
        for key, group in grouped.items():
            # Keep highest OCR confidence
            best_cand = max(group, key=lambda x: x.ocr_confidence)

            # Combined discovery sources
            strategies = set()
            for c in group:
                if c.discovery_strategy:
                    for s in c.discovery_strategy.split(","):
                        strategies.add(s.strip())
            combined_strategy = ", ".join(sorted(strategies))

            # Merge metadata from other candidates in the group
            for c in group:
                if not best_cand.page and c.page:
                    best_cand.page = c.page
                if not best_cand.bounding_box and c.bounding_box:
                    best_cand.bounding_box = c.bounding_box
                if not best_cand.source_line and c.source_line:
                    best_cand.source_line = c.source_line
                if not best_cand.section and c.section:
                    best_cand.section = c.section
                if not best_cand.parent_heading and c.parent_heading:
                    best_cand.parent_heading = c.parent_heading
                if not best_cand.context_window and c.context_window:
                    best_cand.context_window = c.context_window

            best_cand.discovery_strategy = combined_strategy
            best_cand.extraction_strategy = combined_strategy
            merged_list.append(best_cand)

        return merged_list
