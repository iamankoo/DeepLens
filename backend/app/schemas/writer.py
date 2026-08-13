from pydantic import BaseModel

from app.search.schemas import SearchResult


class WriterRequest(BaseModel):

    objective: str

    tasks: list[str]

    sources: list[SearchResult]

    context: str = ""


class WriterResponse(BaseModel):

    report: str