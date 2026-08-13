from app.core.logger import logger
from app.db.models.research_run import ResearchRun
from app.db.repositories.research_run_repository import research_run_repository
from app.db.session import db_manager
from app.jobs.research_job import run_research_job
from app.queue.connection import research_queue
from app.schemas.research import ResearchRequest
from app.utils.id_generator import generate_research_id


class ResearchService:

    def create_research(self, request: ResearchRequest, *, user_id: int | None = None) -> ResearchRun:

        research_id = generate_research_id()

        with db_manager.sync_session_factory() as db:
            run = research_run_repository.create(
                db, research_id=research_id, query=request.query, user_id=user_id
            )

        research_queue.enqueue(run_research_job, research_id, request.query, job_id=research_id)

        logger.info("DeepLens research queued", extra={"research_id": research_id})

        return run


research_service = ResearchService()
