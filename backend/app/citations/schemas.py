from pydantic import BaseModel


class Citation(BaseModel):

    title: str

    url: str

    source: str

    domain: str = ""

    author: str | None = None

    publisher: str | None = None

    published_date: str | None = None

    credibility_score: int = 0


class CitationList(BaseModel):

    citations: list[Citation]