from typing import TypedDict


class ResearchState(TypedDict):

    query: str

    objective: str

    tasks: list[str]

    search_queries: list[str]

    search_results: list[dict]

    ranked_sources: list[dict]

    report: str

    reflection: dict | None

    iteration: int

    max_iterations: int

    memory_results: list = []

    memory_enabled: bool = True

    memory_results: list

    memory_enabled: bool