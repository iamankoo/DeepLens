from pydantic import BaseModel


class QueryRefinementRequest(BaseModel):
    objective: str
    previous_queries: list[str]
    missing_information: list[str]


class QueryRefinementResponse(BaseModel):
    queries: list[str]