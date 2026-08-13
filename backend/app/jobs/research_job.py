from app.agents.research_agent import research_agent
from app.core.logger import logger
from app.db.repositories.research_run_repository import research_run_repository
from app.db.session import db_manager


def run_research_job(research_id: str, query: str) -> str:
    """Entry point executed by the RQ worker process (see `rq worker`
    in README/CLAUDE.md) — runs the full synchronous research pipeline
    off the API request thread and persists the outcome."""

    with db_manager.sync_session_factory() as db:
        research_run_repository.mark_running(db, research_id=research_id)

    logger.info("research job started", extra={"research_id": research_id})

    try:
        result = research_agent.run(query)

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
