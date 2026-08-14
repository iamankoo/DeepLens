from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_current_user_optional
from app.db.models.user import User
from app.db.repositories.research_run_repository import research_run_repository
from app.db.session import get_db
from app.schemas.research import ResearchRequest
from app.schemas.research_run import ResearchRunDetail, ResearchRunSummary
from app.services.research_service import research_service

router = APIRouter()


@router.post("/research", response_model=ResearchRunSummary, status_code=status.HTTP_202_ACCEPTED)
def create_research(request: ResearchRequest, current_user: User | None = Depends(get_current_user_optional)):

    return research_service.create_research(request, user_id=current_user.id if current_user else None)


@router.get("/research", response_model=list[ResearchRunSummary])
async def list_research(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists the current user's own research history. Anonymous (unauthenticated)
    research runs have no owning user and are intentionally not listable here."""

    return await research_run_repository.list_recent(db, user_id=current_user.id, limit=limit, offset=offset)


@router.get("/research/{research_id}", response_model=ResearchRunDetail)
async def get_research(research_id: str, db: AsyncSession = Depends(get_db)):

    run = await research_run_repository.get(db, research_id=research_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run
