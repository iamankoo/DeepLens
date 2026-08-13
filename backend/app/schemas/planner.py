from pydantic import BaseModel, Field


class PlannerRequest(BaseModel):
    query: str = Field(
        ...,
        description="The user's research query."
    )

    previous_research: str = Field(
        default="",
        description="Optional previous research context."
    )


class PlannerResponse(BaseModel):
    objective: str = Field(
        ...,
        description="Overall research objective."
    )

    tasks: list[str] = Field(
        default_factory=list,
        description="Research tasks."
    )