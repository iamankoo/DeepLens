from pydantic import BaseModel


class Citation(BaseModel):

    title: str

    url: str

    source: str

    author: str | None = None

    published_date: str | None = None


class CitationList(BaseModel):

    citations: list[Citation]