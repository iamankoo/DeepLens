from typing import TypedDict
from app.search.schemas import SearchResult
from app.search.chunk import SearchChunk
from app.intelligence.quality_schema import QualityReport


class ResearchState(TypedDict):

    query: str

    objective: str

    tasks: list[str]

    search_queries: list[str]

    search_results: list[SearchResult]

    ranked_sources: list[SearchResult]

    chunk_pool: list[SearchChunk]

    context: str

    report: str

    quality_report: QualityReport | None

    reflection: dict | None

    iteration: int

    max_iterations: int

    memory_results: list

    memory_enabled: bool