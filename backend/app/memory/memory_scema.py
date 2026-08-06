from pydantic import BaseModel
from datetime import datetime


class MemoryRecord(BaseModel):

    id: str

    query: str

    objective: str

    report: str

    created_at: datetime

    metadata: dict = {}