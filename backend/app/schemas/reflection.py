from pydantic import BaseModel


class ReflectionRequest(BaseModel):
    objective: str
    report: str


class ReflectionResponse(BaseModel):
    approved: bool
    feedback: str
    missing_information: list[str]