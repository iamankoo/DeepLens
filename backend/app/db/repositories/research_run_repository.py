from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.models.research_run import ResearchRun, ResearchStatus


class ResearchRunRepository:

    async def list_recent(self, db: AsyncSession, *, limit: int = 20, offset: int = 0) -> list[ResearchRun]:
        result = await db.execute(
            select(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, *, research_id: str) -> ResearchRun | None:
        return await db.get(ResearchRun, research_id)

    def create(self, db: Session, *, research_id: str, query: str) -> ResearchRun:
        run = ResearchRun(id=research_id, query=query, status=ResearchStatus.RUNNING)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def mark_completed(
        self,
        db: Session,
        *,
        research_id: str,
        objective: str,
        report: str,
        iteration: int,
        quality_score: float | None,
    ) -> ResearchRun | None:
        run = db.get(ResearchRun, research_id)
        if run is None:
            return None
        run.status = ResearchStatus.COMPLETED
        run.objective = objective
        run.report = report
        run.iteration = iteration
        run.quality_score = quality_score
        run.completed_at = datetime.now()
        db.commit()
        db.refresh(run)
        return run

    def mark_failed(self, db: Session, *, research_id: str, error: str) -> ResearchRun | None:
        run = db.get(ResearchRun, research_id)
        if run is None:
            return None
        run.status = ResearchStatus.FAILED
        run.error = error
        run.completed_at = datetime.now()
        db.commit()
        db.refresh(run)
        return run


research_run_repository = ResearchRunRepository()
