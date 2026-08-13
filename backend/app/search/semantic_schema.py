from pydantic import BaseModel
from app.search.schemas import SearchResult


class SemanticMatch(BaseModel):
    source: SearchResult
    similarity_score: float