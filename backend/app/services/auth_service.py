from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.models.user import User
from app.db.repositories.refresh_token_repository import refresh_token_repository
from app.db.repositories.user_repository import user_repository
from app.schemas.auth import TokenPair


class AuthService:

    async def register(self, db: AsyncSession, *, email: str, password: str) -> User:
        existing = await user_repository.get_by_email(db, email=email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        # bcrypt hashing is CPU-bound (~100-300ms) — keep it off the event loop.
        hashed = await run_in_threadpool(hash_password, password)
        return await user_repository.create(db, email=email, hashed_password=hashed)

    async def login(self, db: AsyncSession, *, email: str, password: str) -> TokenPair:
        user = await user_repository.get_by_email(db, email=email)
        if user is None or not await run_in_threadpool(verify_password, password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

        return await self._issue_tokens(db, user=user)

    async def refresh(self, db: AsyncSession, *, raw_refresh_token: str) -> TokenPair:
        token_hash = hash_refresh_token(raw_refresh_token)
        token_record = await refresh_token_repository.get_valid_by_hash(db, token_hash=token_hash)
        if token_record is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

        user = await user_repository.get_by_id(db, user_id=token_record.user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

        # Rotation: this refresh token is single-use — revoke it, issue a new pair.
        await refresh_token_repository.revoke(db, token=token_record)
        return await self._issue_tokens(db, user=user)

    async def logout(self, db: AsyncSession, *, raw_refresh_token: str) -> None:
        token_hash = hash_refresh_token(raw_refresh_token)
        token_record = await refresh_token_repository.get_valid_by_hash(db, token_hash=token_hash)
        if token_record is not None:
            await refresh_token_repository.revoke(db, token=token_record)

    async def _issue_tokens(self, db: AsyncSession, *, user: User) -> TokenPair:
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        raw_refresh_token, token_hash, expires_at = generate_refresh_token()
        await refresh_token_repository.create(
            db, user_id=user.id, token_hash=token_hash, expires_at=expires_at
        )
        return TokenPair(access_token=access_token, refresh_token=raw_refresh_token)


auth_service = AuthService()
