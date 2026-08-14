from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.research_run import ResearchStatus


class ResearchRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query: str
    status: ResearchStatus
    quality_score: float | None
    current_step: str | None
    created_at: datetime
    completed_at: datetime | None


class ResearchRunDetail(ResearchRunSummary):
    objective: str | None
    report: str | None
    iteration: int
    error: str | None
