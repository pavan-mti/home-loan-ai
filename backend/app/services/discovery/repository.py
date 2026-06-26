from __future__ import annotations
from ..candidate_model import Candidate

class CandidateRepository:
    def __init__(self, candidates: list[Candidate] = None):
        self.candidates = candidates or []

    def add(self, candidate: Candidate):
        self.candidates.append(candidate)

    def add_all(self, candidates: list[Candidate]):
        self.candidates.extend(candidates)

    def get_all(self) -> list[Candidate]:
        return self.candidates
