from pydantic import BaseModel

from app.intelligence.evidence_level import EvidenceLevel
from app.rewrite.rewrite_strategy import RewriteStrategy


class RewriteSource(BaseModel):

    title: str

    url: str

    snippet: str

    source: str


class RewriteTask(BaseModel):

    paragraph_index: int

    original_paragraph: str

    claims: list[str]

    evidence_level: EvidenceLevel

    rewrite_strategy: RewriteStrategy

    source: RewriteSource | None = None


class RewriteResponse(BaseModel):

    paragraph_index: int

    rewritten_paragraph: str