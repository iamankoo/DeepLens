from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.rate_limit import rate_limit
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    MessageResponse,
    RefreshRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenPair,
    UserLogin,
    UserPublic,
    UserRegister,
    VerifyEmailRequest,
)
from app.services.auth_service import GENERIC_EMAIL_SENT_MESSAGE, auth_service

router = APIRouter()

# Unauthenticated-by-definition endpoints are the classic brute-force /
# credential-stuffing / mass-account-creation / enumeration-via-spam
# targets — every one of them was previously wide open, with no limiting
# anywhere in the stack. Login gets a looser budget than the others since
# legitimate users mistype passwords; account-creation and email-sending
# endpoints get a tighter one since each request has a real cost (a DB row,
# an outbound email) and no legitimate user needs many per hour.
_LOGIN_LIMIT = rate_limit(key_prefix="login", limit=10, window_seconds=300)
_REGISTER_LIMIT = rate_limit(key_prefix="register", limit=5, window_seconds=3600)
_FORGOT_PASSWORD_LIMIT = rate_limit(key_prefix="forgot-password", limit=5, window_seconds=3600)
_RESEND_VERIFICATION_LIMIT = rate_limit(key_prefix="resend-verification", limit=5, window_seconds=3600)
_RESET_PASSWORD_LIMIT = rate_limit(key_prefix="reset-password", limit=10, window_seconds=3600)


@router.post(
    "/auth/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_REGISTER_LIMIT)],
)
async def register(request: UserRegister, db: AsyncSession = Depends(get_db)):

    return await auth_service.register(db, email=request.email, password=request.password, name=request.name)


@router.post("/auth/login", response_model=TokenPair, dependencies=[Depends(_LOGIN_LIMIT)])
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


@router.post("/auth/forgot-password", response_model=MessageResponse, dependencies=[Depends(_FORGOT_PASSWORD_LIMIT)])
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):

    await auth_service.forgot_password(db, email=request.email)
    return MessageResponse(message=GENERIC_EMAIL_SENT_MESSAGE)


@router.post("/auth/reset-password", response_model=MessageResponse, dependencies=[Depends(_RESET_PASSWORD_LIMIT)])
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):

    await auth_service.reset_password(db, raw_token=request.token, new_password=request.new_password)
    return MessageResponse(message="Password has been reset. Please log in again.")


@router.post("/auth/verify-email", response_model=MessageResponse)
async def verify_email(request: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):

    await auth_service.verify_email(db, raw_token=request.token)
    return MessageResponse(message="Email verified.")


@router.post(
    "/auth/resend-verification",
    response_model=MessageResponse,
    dependencies=[Depends(_RESEND_VERIFICATION_LIMIT)],
)
async def resend_verification(request: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):

    await auth_service.resend_verification(db, email=request.email)
    return MessageResponse(message=GENERIC_EMAIL_SENT_MESSAGE)
