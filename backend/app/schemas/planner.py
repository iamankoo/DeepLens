from pydantic import BaseModel


class PlannerResponse(BaseModel):

    objective: str

    tasks: list[str]

class PlannerRequest(BaseModel):

    query: str

    previous_research: str = ""