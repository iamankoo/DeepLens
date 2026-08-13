from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.research import router as research_router
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])

api_router.include_router(auth_router, tags=["Auth"])

api_router.include_router(research_router, tags=["Research"])
