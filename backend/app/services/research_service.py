from rq.job import Callback

from app.core.config import settings
from app.core.logger import logger
from app.db.models.research_run import ResearchRun
from app.db.repositories.research_run_repository import research_run_repository
from app.db.session import db_manager
from app.queue.connection import research_queue
from app.schemas.research import ResearchRequest
from app.utils.id_generator import generate_research_id

# Passed to research_queue.enqueue() as import-path strings, not real
# callables — deliberately avoiding `from app.jobs.research_job import
# run_research_job, handle_research_job_failure` here. That module imports
# app.agents.research_agent -> ... -> app.workflows.nodes, which is what
# instantiates the module-level sentence-transformers/torch model singletons
# (app/search/embedder.py, app/search/cross_encoder.py). The API process
# never runs the research pipeline itself — only the RQ worker does — so
# importing that chain here would load the full ML stack into the API
# service's memory for no reason, on top of the memory-constrained worker
# container this project already has to work around (see
# Settings' "Research pipeline resource limits"). RQ resolves a string
# reference by import path only inside the worker process, at the moment the
# job/callback actually runs — the API process just enqueues the string.
_RUN_RESEARCH_JOB = "app.jobs.research_job.run_research_job"
_HANDLE_RESEARCH_JOB_FAILURE = "app.jobs.research_job.handle_research_job_failure"


class ResearchService:

    def create_research(self, request: ResearchRequest, *, user_id: int | None = None) -> ResearchRun:

        research_id = generate_research_id()

        with db_manager.sync_session_factory() as db:
            run = research_run_repository.create(
                db, research_id=research_id, query=request.query, user_id=user_id
            )

        research_queue.enqueue(
            _RUN_RESEARCH_JOB,
            research_id,
            request.query,
            job_id=research_id,
            job_timeout=settings.RESEARCH_JOB_TIMEOUT_SECONDS,
            # Covers RQ-level failures run_research_job's own try/except can
            # never see: a worker process crash/kill leaves the row stuck at
            # 'running' forever unless something reconciles it — see
            # handle_research_job_failure's docstring for the full trace.
            on_failure=Callback(_HANDLE_RESEARCH_JOB_FAILURE),
            on_stopped=Callback(_HANDLE_RESEARCH_JOB_FAILURE),
        )

        logger.info("DeepLens research queued", extra={"research_id": research_id})

        return run


research_service = ResearchService()
