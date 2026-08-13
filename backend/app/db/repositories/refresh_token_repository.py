from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.refresh_token import RefreshToken


class RefreshTokenRepository:

    async def create(
        self, db: AsyncSession, *, user_id: int, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token

    async def get_valid_by_hash(self, db: AsyncSession, *, token_hash: str) -> RefreshToken | None:
        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        token = result.scalar_one_or_none()
        if token is None:
            return None
        if token.revoked_at is not None:
            return None
        if token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        return token

    async def revoke(self, db: AsyncSession, *, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        await db.commit()

    async def revoke_all_for_user(self, db: AsyncSession, *, user_id: int) -> None:
        """Used on password reset: invalidates every other session so a
        stolen password can't be paired with a still-valid refresh token."""
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await db.commit()


refresh_token_repository = RefreshTokenRepository()
