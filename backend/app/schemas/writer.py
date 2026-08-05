from pydantic import BaseModel


class WriterRequest(BaseModel):

    objective: str

    tasks: list[str]

    sources: list[dict]


class WriterResponse(BaseModel):

    report: str