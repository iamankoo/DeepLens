from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import RefreshRequest, TokenPair, UserLogin, UserPublic, UserRegister
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegister, db: AsyncSession = Depends(get_db)):

    return await auth_service.register(db, email=request.email, password=request.password)


@router.post("/auth/login", response_model=TokenPair)
async def login(request: UserLogin, db: AsyncSession = Depends(get_db)):

    return await auth_service.login(db, email=request.email, password=request.password)


@router.post("/auth/refresh", response_model=TokenPair)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):

    return await auth_service.refresh(db, raw_refresh_token=request.refresh_token)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: RefreshRequest, db: AsyncSession = Depends(get_db)):

    await auth_service.logout(db, raw_refresh_token=request.refresh_token)


@router.get("/auth/me", response_model=UserPublic)
async def me(current_user: User = Depends(get_current_user)):

    return current_user
