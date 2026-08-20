import os
import sys

# Must run before any transformers/torch import happens (via the
# app.jobs.research_job import chain below, which pulls in
# app.search.embedder's SentenceTransformer at module load time). Left at
# their own defaults, torch/OpenBLAS/MKL each spin up a thread pool sized to
# the host's CPU count, and tokenizers' own Rust threadpool does the same —
# on a constrained ~1GB production container this is pure overhead (this
# worker only ever processes one job at a time) that competes with the
# research pipeline's own memory for stack space and buffers, on top of not
# helping latency at this concurrency level. Setting these to single-threaded
# doesn't change model correctness, only how many OS threads back the
# inference call.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from rq import Worker  # noqa: E402
from rq.registry import BaseRegistry  # noqa: E402
from rq.timeouts import get_default_death_penalty_class  # noqa: E402
from rq.worker import SimpleWorker  # noqa: E402

from app.core.logger import logger  # noqa: E402
from app.db.repositories.research_run_repository import research_run_repository  # noqa: E402
from app.db.session import db_manager  # noqa: E402
from app.jobs.research_job import handle_research_job_failure  # noqa: E402
from app.queue.connection import redis_conn, research_queue  # noqa: E402

# Importing research_job above pulls in its full dependency chain
# (app.agents.research_agent -> app.workflows.workflow_manager ->
# research_workflow -> nodes.py), which is what instantiates the module-level
# embedding-model singleton (app/search/embedder.py's SentenceTransformer,
# used immediately by chunking_node right after a source is downloaded).
# Doing that import here, at worker startup in this long-lived parent
# process — rather than letting it happen lazily the first time a job runs —
# matters specifically because RQ's (non-Windows) Worker forks a brand-new
# child process ("work-horse") per job: without this, every single job
# independently loaded its own fresh copy of that transformer model inside
# the forked child, on top of that job's own concurrent page downloads, in
# an already memory-tight ~1GB production container. Loading it once here
# means every forked work-horse inherits the already-loaded weights via the
# OS's ordinary copy-on-write fork semantics instead of reloading its own
# copy — reproduced live in production logs as "Loading weights" appearing
# fresh inside every job's work-horse right as Chunking Node's own
# memory-heavy work was also ramping up.
#
# The cross-encoder model (app/search/cross_encoder.py) is deliberately NOT
# preloaded here despite being pulled in by the same import chain — it's
# lazy-loaded on first actual use (see CrossEncoderRanker.model), because it
# isn't needed until retrieval_node, which runs after chunking_node. Even
# after the above fix plus tightening Chunking's own concurrency/content caps
# (see Settings.EXTRACTION_WORKERS et al.), production still reproduced the
# same OOM within seconds of entering Chunking, with memory metrics showing
# the container at its full ~1GB limit — evidence the cross-encoder's
# resident weights during Chunking's own peak-memory window were part of the
# remaining shortfall despite not being used anywhere near it.


def _patch_registry_death_penalty_for_windows():
    # RQ's own Worker correctly platform-detects its death penalty class via
    # get_default_death_penalty_class() (TimerDeathPenalty when SIGALRM isn't
    # available), but rq.registry.BaseRegistry hardcodes UnixSignalDeathPenalty
    # regardless of platform (rq/registry.py, class attribute). StartedJobRegistry
    # inherits it unchanged, so the moment run_maintenance_tasks() finds an
    # abandoned job and calls job.execute_failure_callback(self.death_penalty_class, ...)
    # during cleanup, it crashes with "AttributeError: module 'signal' has no
    # attribute 'SIGALRM'" on Windows — unhandled, taking down the entire worker
    # process. Reproduced live: a worker died exactly this way while reconciling
    # one abandoned job, right after startup. This isn't our architecture — it's
    # a real cross-platform bug in RQ 2.10.0 — so it's patched once here rather
    # than worked around per-call. Safe cross-platform: uses the same detection
    # RQ's own Worker already relies on, so this is a no-op on Unix.
    BaseRegistry.death_penalty_class = get_default_death_penalty_class()


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


def _handle_work_horse_killed(job, retpid, ret_val, rusage) -> None:
    """Registered as Worker(..., work_horse_killed_handler=...) — RQ's own
    extension point for exactly this scenario (rq/worker/worker_classes.py,
    BaseWorker.monitor_work_horse): it runs synchronously, in this
    still-alive parent process, the instant os.waitpid() confirms the forked
    work-horse child died from an unhandled cause — a crash or, as
    reproduced in production, the container OOM-killing it with SIGKILL
    mid-Chunking-Node.

    This is NOT reached by on_failure/on_stopped (registered at enqueue time
    in research_service.py, handled by handle_research_job_failure below):
    RQ's own handle_job_failure — called immediately alongside this hook for
    a killed work-horse — only updates RQ/Redis-side bookkeeping
    (FailedJobRegistry, Result) for that path; Job._handle_failure() never
    calls execute_failure_callback there (confirmed from rq's own source,
    job.py). That gap is exactly why a killed work-horse's ResearchRun
    stayed at 'running' forever in production: nothing updated it until a
    future worker restart's _reconcile_orphaned_runs(), or RQ's own
    AbandonedJobError sweep — which only fires once the job's full
    RESEARCH_JOB_TIMEOUT_SECONDS budget has elapsed. Reusing
    handle_research_job_failure here (same guard against ever overwriting a
    run that already finished normally) gives a killed work-horse the exact
    same ResearchRun -> FAILED treatment, just immediately instead of
    minutes-to-never later."""
    handle_research_job_failure(job, redis_conn)


def main():
    # RQ's default Worker forks a child process per job (os.fork), which
    # doesn't exist on Windows and silently never dequeues anything there —
    # SimpleWorker runs jobs in-process instead and is the supported choice
    # on this platform.
    worker_cls = SimpleWorker if sys.platform == "win32" else Worker

    _patch_registry_death_penalty_for_windows()

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

    # work_horse_killed_handler is a no-op under SimpleWorker (it never forks
    # a work-horse to begin with — see the platform branch above) but is
    # harmless to pass either way; kept unconditional so this isn't something
    # a future edit could silently drop for one platform.
    worker = worker_cls(
        [research_queue],
        connection=redis_conn,
        work_horse_killed_handler=_handle_work_horse_killed,
    )
    worker.work()


if __name__ == "__main__":
    main()
