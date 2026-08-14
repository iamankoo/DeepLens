import sys

from rq import Worker
from rq.worker import SimpleWorker

from app.core.logger import logger
from app.db.repositories.research_run_repository import research_run_repository
from app.db.session import db_manager
from app.queue.connection import redis_conn, research_queue


def _reconcile_orphaned_runs():
    # A fresh worker process cannot possibly have any job legitimately
    # in flight yet — any ResearchRun still 'running' at this exact moment
    # belongs to a previous worker process that died without reaching its
    # own except block. Doing this here is immediate, unlike RQ's own
    # abandoned-job detection which only fires once a job's full timeout
    # budget (RESEARCH_JOB_TIMEOUT_SECONDS, up to 30 minutes) has elapsed —
    # see mark_orphaned_running_as_failed's docstring for how this was found.
    with db_manager.sync_session_factory() as db:
        orphaned_ids = research_run_repository.mark_orphaned_running_as_failed(
            db,
            error="The research worker restarted before this run could finish "
            "(process crash or restart). Please try again.",
        )
    if orphaned_ids:
        logger.warning(
            "reconciled orphaned research runs at worker startup",
            extra={"count": len(orphaned_ids), "research_ids": orphaned_ids},
        )


def main():
    # RQ's default Worker forks a child process per job (os.fork), which
    # doesn't exist on Windows and silently never dequeues anything there —
    # SimpleWorker runs jobs in-process instead and is the supported choice
    # on this platform.
    worker_cls = SimpleWorker if sys.platform == "win32" else Worker

    logger.info(
        "starting RQ worker",
        extra={"worker_class": worker_cls.__name__, "queue": research_queue.name},
    )

    # RQ resolves the job function by import path only when a job actually
    # runs, not at worker startup — so provider_registry (and its
    # registration-time "is_available" log line) wouldn't otherwise exist
    # in this process until the first job executes. Importing it here
    # forces that logging to happen at worker boot, matching what the API
    # process already does at its own startup.
    from app.providers.llm.registry import provider_registry  # noqa: F401

    _reconcile_orphaned_runs()

    worker = worker_cls([research_queue], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
