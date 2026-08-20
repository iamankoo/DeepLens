"""Focused tests for the read-time staleness reconciliation added to
ResearchRunRepository.get()/list_recent() — a second, independent line of
defense against an orphaned 'running'/'pending' row on top of worker-side
reconciliation (on_failure/on_stopped, work_horse_killed_handler,
_reconcile_orphaned_runs at worker boot; see app/worker.py and
app/jobs/research_job.py). Those all depend on the worker process itself
doing something; this instead self-heals on the next GET /research/{id}
poll, independent of whatever state the worker process is actually in.

Also guards the specific bug this logic was found to have during manual
testing: comparing a MySQL server-side UTC timestamp against Python's
datetime.now() (this dev machine is IST, UTC+5:30) marked every row stale
within about a second of creation. And the follow-up design bug: measuring
a RUNNING row's staleness from created_at (enqueue time) instead of
started_at (when the worker actually began executing it) could mark a row
FAILED before the worker even got to start it, on a single worker still
processing an earlier queued job."""

from datetime import datetime, timedelta

import pytest

from app.db.models.research_run import ResearchStatus
from app.db.repositories.research_run_repository import research_run_repository
from app.db.session import db_manager
from app.utils.id_generator import generate_research_id


@pytest.mark.asyncio
async def test_stale_running_row_is_reconciled_on_read(monkeypatch):
    from app.db.repositories import research_run_repository as repo_module

    monkeypatch.setattr(repo_module.settings, "RESEARCH_JOB_TIMEOUT_SECONDS", 10)

    research_id = generate_research_id()

    with db_manager.sync_session_factory() as db:
        research_run_repository.create(db, research_id=research_id, query="staleness test")
        run = research_run_repository.mark_running(db, research_id=research_id)
        # Simulate a worker that started this run well over the (tiny,
        # monkeypatched) timeout ago and then vanished without a trace —
        # the scenario none of the worker-side reconciliation paths cover
        # if the worker process itself never restarts.
        run.started_at = datetime.utcnow() - timedelta(seconds=120)
        db.commit()

    async with db_manager.session_factory() as adb:
        result = await research_run_repository.get(adb, research_id=research_id)

    assert result.status == ResearchStatus.FAILED
    assert result.error is not None and "maximum allowed duration" in result.error
    assert result.completed_at is not None


@pytest.mark.asyncio
async def test_freshly_started_running_row_is_left_alone():
    research_id = generate_research_id()

    with db_manager.sync_session_factory() as db:
        research_run_repository.create(db, research_id=research_id, query="staleness test")
        research_run_repository.mark_running(db, research_id=research_id)

    async with db_manager.session_factory() as adb:
        result = await research_run_repository.get(adb, research_id=research_id)

    assert result.status == ResearchStatus.RUNNING


@pytest.mark.asyncio
async def test_pending_row_queued_behind_a_busy_worker_is_not_falsely_reconciled(monkeypatch):
    """A PENDING row (not yet picked up by the worker) must tolerate a
    normal queue wait — even one longer than RESEARCH_JOB_TIMEOUT_SECONDS —
    since it hasn't started executing yet and carries none of that
    timeout's risk. Only RUNNING rows are measured against the tight
    execution deadline."""

    from app.db.repositories import research_run_repository as repo_module

    monkeypatch.setattr(repo_module.settings, "RESEARCH_JOB_TIMEOUT_SECONDS", 10)

    research_id = generate_research_id()

    with db_manager.sync_session_factory() as db:
        run = research_run_repository.create(db, research_id=research_id, query="staleness test")
        # Still PENDING, created well past the (tiny, monkeypatched)
        # RESEARCH_JOB_TIMEOUT_SECONDS + grace, but nowhere near
        # _PENDING_STALENESS_SECONDS.
        run.created_at = datetime.utcnow() - timedelta(seconds=60)
        db.commit()

    async with db_manager.session_factory() as adb:
        result = await research_run_repository.get(adb, research_id=research_id)

    assert result.status == ResearchStatus.PENDING
