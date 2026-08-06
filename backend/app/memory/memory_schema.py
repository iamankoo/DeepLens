from datetime import datetime

from pydantic import BaseModel, Field


class MemoryRecord(BaseModel):
    """
    Represents a single research memory stored in the vector database.
    """

    id: str

    query: str

    objective: str

    report: str

    created_at: datetime

    metadata: dict = Field(default_factory=dict)