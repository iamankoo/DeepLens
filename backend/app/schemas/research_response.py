from pydantic import BaseModel

from app.search.schemas import SearchResult


class ResearchPlan(BaseModel):
    query: str
    objective: str
    tasks: list[str]
    search_queries: list[str]
    ranked_sources: list[SearchResult]
    report: str
    iteration: int
    quality_score: float | None = None
    approved: bool | None = None


class ResearchResponse(BaseModel):
    research_id: str
    status: str
    message: str
    plan: ResearchPlan
