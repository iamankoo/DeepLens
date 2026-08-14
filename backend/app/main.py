from contextlib import asynccontextmanager

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import DeepLensError, LLMProviderError, OutputParsingError
from app.core.logger import logger
from app.db.session import db_manager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Mirrors app/worker.py's eager import: provider_registry is otherwise
    # only instantiated lazily on first use, so its "is_available" log line
    # (useful for confirming which providers a fresh process actually sees
    # as configured) wouldn't appear at boot without this.
    from app.providers.llm.registry import provider_registry  # noqa: F401

    logger.info("DeepLens API starting", extra={"version": settings.APP_VERSION, "debug": settings.DEBUG})
    yield
    await db_manager.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(LLMProviderError)
async def llm_provider_error_handler(request: Request, exc: LLMProviderError):
    logger.error("LLM provider error", extra={"path": request.url.path, "error": str(exc)})
    return JSONResponse(
        status_code=502,
        content={"error": "llm_provider_error", "detail": str(exc)},
    )


@app.exception_handler(OutputParsingError)
async def output_parsing_error_handler(request: Request, exc: OutputParsingError):
    logger.error("Output parsing error", extra={"path": request.url.path, "error": str(exc)})
    return JSONResponse(
        status_code=502,
        content={"error": "output_parsing_error", "detail": str(exc)},
    )


@app.exception_handler(DeepLensError)
async def deeplens_error_handler(request: Request, exc: DeepLensError):
    logger.error("Application error", extra={"path": request.url.path, "error": str(exc)})
    return JSONResponse(
        status_code=500,
        content={"error": "application_error", "detail": str(exc)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": "An unexpected error occurred."},
    )


@app.get("/")
def root():
    return {
        "message": "Welcome to DeepLens 🚀",
        "made_by": "Aniket ❤️",
        "tagline": "Made with Love by Aniket Raj",
    }
