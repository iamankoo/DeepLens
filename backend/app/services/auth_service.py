from datetime import timedelta

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import email_sender
from app.core.logger import logger
from app.core.security import (
    create_access_token,
    generate_email_token,
    generate_refresh_token,
    hash_email_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.models.email_token import EmailTokenPurpose
from app.db.models.user import User
from app.db.repositories.email_token_repository import email_token_repository
from app.db.repositories.refresh_token_repository import refresh_token_repository
from app.db.repositories.user_repository import user_repository
from app.schemas.auth import TokenPair

# Generic responses for anything keyed by "does this email exist" — never
# let register/forgot-password/resend-verification reveal whether an
# account exists for a given address.
GENERIC_EMAIL_SENT_MESSAGE = "If that email is registered, a message has been sent."


class AuthService:

    async def register(self, db: AsyncSession, *, email: str, password: str, name: str) -> User:
        existing = await user_repository.get_by_email(db, email=email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        # bcrypt hashing is CPU-bound (~100-300ms) — keep it off the event loop.
        hashed = await run_in_threadpool(hash_password, password)
        user = await user_repository.create(db, email=email, hashed_password=hashed, name=name)

        await self._send_verification_email(db, user=user)
        return user

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

    async def forgot_password(self, db: AsyncSession, *, email: str) -> None:
        user = await user_repository.get_by_email(db, email=email)
        if user is None:
            return  # generic response at the endpoint layer either way

        raw_token, token_hash, expires_at = generate_email_token(
            expires_delta=timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        )
        await email_token_repository.create(
            db,
            user_id=user.id,
            token_hash=token_hash,
            purpose=EmailTokenPurpose.PASSWORD_RESET,
            expires_at=expires_at,
        )

        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        await run_in_threadpool(
            email_sender.send,
            to=user.email,
            subject="Reset your DeepLens password",
            body=f"Reset your password: {reset_link}\n\nThis link expires in "
            f"{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes. "
            f"If you didn't request this, ignore this email.",
        )

    async def reset_password(self, db: AsyncSession, *, raw_token: str, new_password: str) -> None:
        token_hash = hash_email_token(raw_token)
        token_record = await email_token_repository.get_valid_by_hash(
            db, token_hash=token_hash, purpose=EmailTokenPurpose.PASSWORD_RESET
        )
        if token_record is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

        user = await user_repository.get_by_id(db, user_id=token_record.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

        hashed = await run_in_threadpool(hash_password, new_password)
        await user_repository.update_password(db, user=user, hashed_password=hashed)
        await email_token_repository.mark_used(db, token=token_record)

        # A leaked password is often paired with a still-valid session —
        # close every existing session on password change.
        await refresh_token_repository.revoke_all_for_user(db, user_id=user.id)

    async def resend_verification(self, db: AsyncSession, *, email: str) -> None:
        user = await user_repository.get_by_email(db, email=email)
        if user is None or user.email_verified:
            return  # generic response at the endpoint layer either way
        await self._send_verification_email(db, user=user)

    async def verify_email(self, db: AsyncSession, *, raw_token: str) -> None:
        token_hash = hash_email_token(raw_token)
        token_record = await email_token_repository.get_valid_by_hash(
            db, token_hash=token_hash, purpose=EmailTokenPurpose.EMAIL_VERIFICATION
        )
        if token_record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token"
            )

        user = await user_repository.get_by_id(db, user_id=token_record.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token"
            )

        await user_repository.mark_email_verified(db, user=user)
        await email_token_repository.mark_used(db, token=token_record)

    async def _send_verification_email(self, db: AsyncSession, *, user: User) -> None:
        raw_token, token_hash, expires_at = generate_email_token(
            expires_delta=timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
        )
        await email_token_repository.create(
            db,
            user_id=user.id,
            token_hash=token_hash,
            purpose=EmailTokenPurpose.EMAIL_VERIFICATION,
            expires_at=expires_at,
        )

        verify_link = f"{settings.FRONTEND_URL}/verify-email?token={raw_token}"
        try:
            await run_in_threadpool(
                email_sender.send,
                to=user.email,
                subject="Verify your DeepLens email",
                body=f"Verify your email: {verify_link}\n\nThis link expires in "
                f"{settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} hours.",
            )
        except Exception:
            # Verification is non-blocking — a broken SMTP config shouldn't
            # fail registration itself.
            logger.exception("failed to send verification email", extra={"user_id": user.id})

    async def _issue_tokens(self, db: AsyncSession, *, user: User) -> TokenPair:
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        raw_refresh_token, token_hash, expires_at = generate_refresh_token()
        await refresh_token_repository.create(
            db, user_id=user.id, token_hash=token_hash, expires_at=expires_at
        )
        return TokenPair(access_token=access_token, refresh_token=raw_refresh_token)


auth_service = AuthService()
