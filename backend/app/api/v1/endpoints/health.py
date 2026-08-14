from fastapi import APIRouter

from app.core.config import settings
from app.providers.llm.health import provider_health

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}


@router.get("/health/providers")
def provider_health_check():
    """Per-provider status/latency/success-rate, tracked by the worker
    process since it last restarted (see app/providers/llm/health.py) —
    not the API process, since LLM calls happen in the RQ worker."""

    return {"providers": provider_health.snapshot()}
