from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.research_run import ResearchRun, ResearchStatus

# Extra grace beyond RESEARCH_JOB_TIMEOUT_SECONDS before a still-running row
# is considered stale enough to reconcile on read — covers the real, normal
# time between "RQ's job_timeout fires" and "the callback/except block
# actually finishes writing FAILED to the database", not just clock skew.
# Kept short since RESEARCH_JOB_TIMEOUT_SECONDS is itself now the
# product-required 120s hard maximum, not the old 30-minute budget.
_STALENESS_GRACE_SECONDS = 30

# A PENDING row (enqueued but not yet picked up by a worker) has no
# execution-time risk the way a RUNNING one does — it's just waiting for a
# worker slot, which can legitimately take a while on a single-worker
# deployment under a real backlog of earlier requests. This is deliberately
# much larger than RESEARCH_JOB_TIMEOUT_SECONDS so a normal queue wait is
# never mistaken for an orphaned row; it only exists to eventually self-heal
# a row whose enqueue genuinely never produced a job a worker will ever see
# (e.g. Redis was unreachable at the moment of enqueue).
_PENDING_STALENESS_SECONDS = 900


def _reconcile_if_stale(run: ResearchRun) -> bool:
    """Returns True if `run` was rewritten in place to FAILED.

    This is a second, independent line of defense against an orphaned
    'running'/'pending' row, on top of worker-side reconciliation (RQ's
    on_failure/on_stopped callbacks, the work_horse_killed_handler, and
    _reconcile_orphaned_runs() at worker boot — see app/worker.py and
    app/jobs/research_job.py). All of those depend on the worker process
    itself doing something: catching an exception, detecting a killed
    work-horse, or restarting. If the worker process is simply gone and
    nothing restarts it, none of them ever fire, and the row would stay
    'running' forever with no bound. Checking staleness here instead, right
    where the frontend already polls (GET /research/{id}), needs no worker
    involvement at all — every poll after RESEARCH_JOB_TIMEOUT_SECONDS +
    grace has elapsed since creation self-heals the row on the next read,
    independent of whatever state the worker process is actually in."""

    if run.status not in (ResearchStatus.PENDING, ResearchStatus.RUNNING):
        return False

    # `created_at`/`started_at` are MySQL server-side/app-UTC timestamps —
    # verified live against this project's own dev database that MySQL's
    # NOW() is UTC in this container. This machine's local time is IST
    # (UTC+5:30); comparing against datetime.now() here previously made
    # every row look 5.5 hours old the instant it was created, marking it
    # FAILED within about a second of being enqueued — reproduced live.
    # datetime.utcnow() is the correct comparison against values that came
    # from (or are meant to line up with) the database.
    now = datetime.utcnow()

    if run.status == ResearchStatus.RUNNING:
        # Measured from started_at (when the worker actually began
        # executing this run), not created_at (when it was enqueued) — a
        # run can legitimately sit queued for a while behind an earlier job
        # on a single worker. A RUNNING row with no started_at shouldn't be
        # possible (mark_running always sets it) but falls back to
        # created_at defensively rather than never going stale.
        anchor = run.started_at or run.created_at
        deadline = anchor + timedelta(seconds=settings.RESEARCH_JOB_TIMEOUT_SECONDS + _STALENESS_GRACE_SECONDS)
    else:
        deadline = run.created_at + timedelta(seconds=_PENDING_STALENESS_SECONDS)

    if now < deadline:
        return False

    run.status = ResearchStatus.FAILED
    run.error = (
        "This research run exceeded the maximum allowed duration "
        f"({settings.RESEARCH_JOB_TIMEOUT_SECONDS}s) and was automatically marked as failed. "
        "Please try again."
    )
    run.completed_at = now
    return True


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
        runs = list(result.scalars().all())
        if any(_reconcile_if_stale(run) for run in runs):
            await db.commit()
        return runs

    async def get(self, db: AsyncSession, *, research_id: str) -> ResearchRun | None:
        run = await db.get(ResearchRun, research_id)
        if run is not None and _reconcile_if_stale(run):
            await db.commit()
            await db.refresh(run)
        return run

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
        run.started_at = datetime.utcnow()
        # A retried/re-picked-up run (rare, but possible if a run is ever
        # manually reset to pending) shouldn't carry a stale error/
        # completed_at from a previous attempt into a fresh run that's
        # actively in progress again.
        run.error = None
        run.completed_at = None
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
