from app.schemas.research import ResearchRequest
from app.schemas.research_response import ResearchResponse
from app.services.research_service import research_service
from fastapi import APIRouter

router = APIRouter()


@router.post("/research", response_model=ResearchResponse)
def create_research(request: ResearchRequest):

    return research_service.create_research(request)
