from pydantic import BaseModel

from app.search.chunk import SearchChunk


class SearchDocument(BaseModel):

    title: str

    url: str

    source: str

    domain: str

    content: str

    chunks: list[SearchChunk] = []