from pydantic import BaseModel


class SearchChunk(BaseModel):

    chunk_id: int

    text: str

    embedding: list[float] | None = None

    similarity: float = 0.0

    start_sentence: int

    end_sentence: int

    source_url: str

    source_title: str

    source_name: str | None = None