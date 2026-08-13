from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import DeepLensError, LLMProviderError, OutputParsingError
from app.core.logger import logger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
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
