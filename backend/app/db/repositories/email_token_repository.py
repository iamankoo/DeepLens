from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.email_token import EmailToken, EmailTokenPurpose


class EmailTokenRepository:

    async def create(
        self, db: AsyncSession, *, user_id: int, token_hash: str, purpose: EmailTokenPurpose, expires_at: datetime
    ) -> EmailToken:
        token = EmailToken(user_id=user_id, token_hash=token_hash, purpose=purpose, expires_at=expires_at)
        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token

    async def get_valid_by_hash(
        self, db: AsyncSession, *, token_hash: str, purpose: EmailTokenPurpose
    ) -> EmailToken | None:
        result = await db.execute(
            select(EmailToken).where(EmailToken.token_hash == token_hash, EmailToken.purpose == purpose)
        )
        token = result.scalar_one_or_none()
        if token is None:
            return None
        if token.used_at is not None:
            return None
        if token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        return token

    async def mark_used(self, db: AsyncSession, *, token: EmailToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        await db.commit()


email_token_repository = EmailTokenRepository()
