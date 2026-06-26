from __future__ import annotations
from typing import TYPE_CHECKING
from ..candidate_model import Candidate

if TYPE_CHECKING:
    from .index import DocumentIndex

class BaseDiscoveryStrategy:
    def discover(self, context: DocumentIndex) -> list[Candidate]:
        """
        Analyze the document index and yield found candidates placeholder-independently.
        """
        raise NotImplementedError("Subclasses must implement the discover method")
