from pydantic import BaseModel


class SearchResult(BaseModel):

    title: str

    url: str

    snippet: str

    source: str = ""

    domain: str = ""

    author: str | None = None

    published_date: str | None = None

    credibility_score: int = 0

    embedding: list[float] | None = None