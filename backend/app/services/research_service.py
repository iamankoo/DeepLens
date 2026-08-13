from fastapi import HTTPException

from app.core.exceptions import DeepLensError
from app.core.logger import logger
from app.schemas.research import ResearchRequest
from app.schemas.research_response import ResearchResponse
from app.utils.id_generator import generate_research_id
from app.agents.research_agent import research_agent


class ResearchService:

    def create_research(self, request: ResearchRequest) -> ResearchResponse:

        research_id = generate_research_id()

        try:

            logger.info("DeepLens research started", extra={"research_id": research_id})

            result = research_agent.run(request.query)

            quality_report = result.get("quality_report")
            reflection = result.get("reflection")

            logger.info(
                "DeepLens research completed",
                extra={"research_id": research_id, "iterations": result.get("iteration", 0)},
            )

            return ResearchResponse(
                research_id=research_id,
                status="completed",
                message="Research completed",
                plan={
                    "query": result.get("query", request.query),
                    "objective": result.get("objective", ""),
                    "tasks": result.get("tasks", []),
                    "search_queries": result.get("search_queries", []),
                    "ranked_sources": result.get("ranked_sources", []),
                    "report": result.get("report", ""),
                    "iteration": result.get("iteration", 0),
                    "quality_score": quality_report.overall_score if quality_report else None,
                    "approved": reflection.get("approved") if reflection else None,
                },
            )

        except DeepLensError:

            # Let FastAPI's typed exception handlers (main.py) format the response
            # (e.g. 502 for upstream LLM/parsing failures vs. 500 for app bugs).
            logger.exception("DeepLens research failed", extra={"research_id": research_id})
            raise

        except Exception as e:

            logger.exception("DeepLens research failed", extra={"research_id": research_id})

            raise HTTPException(
                status_code=500,
                detail=str(e),
            )


research_service = ResearchService()