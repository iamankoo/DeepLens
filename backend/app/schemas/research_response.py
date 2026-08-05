from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class Report(BaseModel):
    title: str
    executive_summary: str
    objectives: list[str]
    tasks: list[str]
    sources: list[SearchResult]


class ResearchPlan(BaseModel):
    query: str
    objective: str
    tasks: list[str]

    search_queries: list[str]
    search_results: list[SearchResult]
    ranked_sources: list[SearchResult]

    report: Report


class ResearchResponse(BaseModel):
    research_id: str
    status: str
    message: str
    plan: ResearchPlan
