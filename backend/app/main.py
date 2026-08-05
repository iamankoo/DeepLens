from app.api.v1.router import api_router
from app.core.config import settings
from fastapi import FastAPI

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Welcome to DeepLens 🚀",
        "made_by": "Aniket ❤️",
        "tagline": "Made with Love by Aniket Raj",
    }
