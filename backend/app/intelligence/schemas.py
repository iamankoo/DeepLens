from pydantic import BaseModel

from app.intelligence.evidence_level import (
    EvidenceLevel,
)
from app.search.chunk import SearchChunk


class EvidenceResult(BaseModel):

    paragraph: str

    evidence_level: EvidenceLevel

    supported: bool

    hallucination: bool

    similarity_score: float

    confidence: float

    best_chunk: SearchChunk | None = None