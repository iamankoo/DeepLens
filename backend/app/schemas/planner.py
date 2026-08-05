from pydantic import BaseModel


class PlannerResponse(BaseModel):

    objective: str

    tasks: list[str]