from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.models.research_run import ResearchRun, ResearchStatus


class ResearchRunRepository:

    async def list_recent(
        self, db: AsyncSession, *, user_id: int, limit: int = 20, offset: int = 0
    ) -> list[ResearchRun]:
        result = await db.execute(
            select(ResearchRun)
            .where(ResearchRun.user_id == user_id)
            .order_by(ResearchRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, *, research_id: str) -> ResearchRun | None:
        return await db.get(ResearchRun, research_id)

    def get_sync(self, db: Session, *, research_id: str) -> ResearchRun | None:
        return db.get(ResearchRun, research_id)

    def create(
        self, db: Session, *, research_id: str, query: str, user_id: int | None = None
    ) -> ResearchRun:
        run = ResearchRun(id=research_id, query=query, status=ResearchStatus.PENDING, user_id=user_id)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def mark_running(self, db: Session, *, research_id: str) -> ResearchRun | None:
        run = db.get(ResearchRun, research_id)
        if run is None:
            return None
        run.status = ResearchStatus.RUNNING
        db.commit()
        db.refresh(run)
        return run

    def update_step(self, db: Session, *, research_id: str, step: str) -> None:
        run = db.get(ResearchRun, research_id)
        if run is None:
            return
        run.current_step = step
        db.commit()

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

    def mark_orphaned_running_as_failed(self, db: Session, *, error: str) -> list[str]:
        """A SimpleWorker processes exactly one job at a time — so at the
        exact moment a worker process boots, it cannot possibly have any
        job legitimately in flight yet. Any ResearchRun still 'running' at
        that instant belongs to a *previous* worker process that died
        without reaching its own except block (crash, OOM, force-kill).

        This exists because RQ's own abandoned-job detection
        (StartedJobRegistry.cleanup(), see handle_research_job_failure)
        only fires once a job's *own* timeout budget has elapsed — with
        RESEARCH_JOB_TIMEOUT_SECONDS=1800, that's up to 30 minutes of a
        truly-dead job silently sitting at 'running' before RQ notices.
        Reproduced live: a worker crash left a row stuck at 'running' with
        RQ still reporting it as JobStatus.STARTED and not yet expired.
        This check is immediate instead of dependent on that timeout."""

        rows = db.execute(select(ResearchRun).where(ResearchRun.status == ResearchStatus.RUNNING)).scalars().all()
        ids = [run.id for run in rows]
        for run in rows:
            run.status = ResearchStatus.FAILED
            run.error = error
            run.completed_at = datetime.now()
        if rows:
            db.commit()
        return ids


research_run_repository = ResearchRunRepository()
