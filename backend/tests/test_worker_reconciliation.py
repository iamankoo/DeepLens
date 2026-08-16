"""Focused tests for the second half of the OOM-hang fix: a research job
whose RQ work-horse is killed unexpectedly (crash/OOM/SIGKILL) must not leave
its ResearchRun stuck at 'running' forever. Exercises the real DB-writing
guard logic (research_run_repository, handle_research_job_failure,
app.worker's work_horse_killed_handler wiring) against a live database —
matches this project's existing precedent of DB/queue-adjacent behavior being
verified against a real MySQL rather than mocked (see CLAUDE.md), and needs a
real row to prove the "never overwrite a run that already finished" guard."""

from types import SimpleNamespace

from app.db.models.research_run import ResearchStatus
from app.db.repositories.research_run_repository import research_run_repository
from app.db.session import db_manager
from app.jobs.research_job import handle_research_job_failure
from app.utils.id_generator import generate_research_id
from app.worker import _handle_work_horse_killed


def _fake_job(research_id: str):
    # handle_research_job_failure only ever reads job.args[0]; a plain
    # namespace is enough to exercise it without real RQ machinery.
    return SimpleNamespace(args=[research_id])


def test_work_horse_killed_marks_running_run_as_failed():
    research_id = generate_research_id()

    with db_manager.sync_session_factory() as db:
        research_run_repository.create(db, research_id=research_id, query="test query")
        research_run_repository.mark_running(db, research_id=research_id)

    _handle_work_horse_killed(_fake_job(research_id), retpid=1234, ret_val=9, rusage=None)

    with db_manager.sync_session_factory() as db:
        run = research_run_repository.get_sync(db, research_id=research_id)
        assert run.status == ResearchStatus.FAILED
        assert run.error is not None and len(run.error) > 0
        assert run.completed_at is not None


def test_work_horse_killed_does_not_overwrite_a_completed_run():
    research_id = generate_research_id()

    with db_manager.sync_session_factory() as db:
        research_run_repository.create(db, research_id=research_id, query="test query")
        research_run_repository.mark_running(db, research_id=research_id)
        research_run_repository.mark_completed(
            db,
            research_id=research_id,
            objective="test objective",
            report="a real, non-empty report",
            iteration=1,
            quality_score=0.9,
        )

    # A stale/duplicate work-horse-killed signal for an already-finished job
    # (e.g. RQ's monitor loop and this hook both observing the same exit)
    # must never clobber the real completed result.
    handle_research_job_failure(_fake_job(research_id), connection=None)

    with db_manager.sync_session_factory() as db:
        run = research_run_repository.get_sync(db, research_id=research_id)
        assert run.status == ResearchStatus.COMPLETED
        assert run.report == "a real, non-empty report"


def test_work_horse_killed_does_not_overwrite_a_specific_prior_error():
    """run_research_job's own except block may have already recorded a
    specific, useful error before the process died — the generic work-horse
    message must not stomp it."""

    research_id = generate_research_id()

    with db_manager.sync_session_factory() as db:
        research_run_repository.create(db, research_id=research_id, query="test query")
        research_run_repository.mark_running(db, research_id=research_id)
        research_run_repository.mark_failed(
            db, research_id=research_id, error="Tavily API key invalid"
        )

    _handle_work_horse_killed(_fake_job(research_id), retpid=1234, ret_val=9, rusage=None)

    with db_manager.sync_session_factory() as db:
        run = research_run_repository.get_sync(db, research_id=research_id)
        assert run.status == ResearchStatus.FAILED
        assert run.error == "Tavily API key invalid"
