from app.agents.research_agent import research_agent
from app.core.logger import logger
from app.db.models.research_run import ResearchStatus
from app.db.repositories.research_run_repository import research_run_repository
from app.db.session import db_manager


def handle_research_job_failure(job, connection, *exc_info) -> None:
    """Registered as research_queue.enqueue(..., on_failure=..., on_stopped=...)
    AND called directly by app/worker.py's _handle_work_horse_killed.

    Covers the failure paths run_research_job's own try/except can't:
    if the worker process dies mid-job (crash, OOM, a forced restart —
    all reproduced during development), the process is gone before its
    except block ever runs, so the ResearchRun row is orphaned at
    'running' forever. Two independent things call this for that case:
    (1) app/worker.py's work_horse_killed_handler, immediately, the instant
    the parent worker process detects a forked work-horse died unexpectedly
    (the common production case — reproduced live as a container OOM/SIGKILL
    mid-Chunking-Node); and (2) RQ's own AbandonedJobError sweep
    (StartedJobRegistry.cleanup()), as a slower fallback for cases (1) can't
    cover — e.g. the parent worker process itself dying — which only fires
    once a job's full timeout budget has elapsed, or at the next worker
    startup (see _reconcile_orphaned_runs, a third, DB-side independent
    check for that same startup case).

    Guarded by current status so this never overwrites a specific error
    already recorded by run_research_job's own except block for a normal
    in-process failure, and so a job already reconciled by one of the paths
    above is never double-processed by another (all can fire for the same
    job)."""

    research_id = job.args[0]

    with db_manager.sync_session_factory() as db:
        run = research_run_repository.get_sync(db, research_id=research_id)
        if run is None or run.status not in (ResearchStatus.PENDING, ResearchStatus.RUNNING):
            return

        logger.error(
            "research job abandoned or crashed outside its own exception handler",
            extra={"research_id": research_id},
        )
        research_run_repository.mark_failed(
            db,
            research_id=research_id,
            error="The research worker stopped unexpectedly before this run could finish "
            "(process crash or restart). Please try again.",
        )


def run_research_job(research_id: str, query: str) -> str:
    """Entry point executed by the RQ worker process — runs the full
    synchronous research pipeline off the API request thread and
    persists the outcome."""

    with db_manager.sync_session_factory() as db:
        research_run_repository.mark_running(db, research_id=research_id)

    logger.info("research job started", extra={"research_id": research_id})

    def on_step(step: str) -> None:
        with db_manager.sync_session_factory() as db:
            research_run_repository.update_step(db, research_id=research_id, step=step)

    try:
        result = research_agent.run(query, on_step=on_step)

        quality_report = result.get("quality_report")

        with db_manager.sync_session_factory() as db:
            research_run_repository.mark_completed(
                db,
                research_id=research_id,
                objective=result.get("objective", ""),
                report=result.get("report", ""),
                iteration=result.get("iteration", 0),
                quality_score=quality_report.overall_score if quality_report else None,
            )

        logger.info("research job completed", extra={"research_id": research_id})

    except Exception as e:

        logger.exception("research job failed", extra={"research_id": research_id})

        with db_manager.sync_session_factory() as db:
            research_run_repository.mark_failed(db, research_id=research_id, error=str(e))

        raise

    return research_id
