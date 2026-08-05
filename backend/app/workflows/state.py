from typing import TypedDict


class ResearchState(TypedDict):
    query: str
    objective: str
    tasks: list[str]

    search_queries: list[str]
    search_results: list[dict]

    ranked_sources: list[dict]

    report: dict
