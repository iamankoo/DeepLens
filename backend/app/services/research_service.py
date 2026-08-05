from fastapi import HTTPException

from app.core.logger import logger
from app.schemas.research import ResearchRequest
from app.utils.id_generator import generate_research_id
from app.workflows.research_workflow import research_graph


class ResearchService:

    def create_research(self, request: ResearchRequest):

        try:

            logger.info("=" * 60)
            logger.info("DeepLens Research Started")
            logger.info(f"Query: {request.query}")

            result = research_graph.invoke(
                {
                    "query": request.query
                }
            )

            research_id = generate_research_id()

            logger.info(f"Research ID: {research_id}")
            logger.info("DeepLens Research Completed")
            logger.info("=" * 60)

            return {
                "research_id": research_id,
                "status": "planning",
                "message": "Research started",
                "plan": result,
            }

        except Exception as e:

            logger.exception("Research Failed")

            raise HTTPException(
                status_code=500,
                detail=str(e)
            )


research_service = ResearchService()