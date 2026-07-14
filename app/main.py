import asyncio
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.openai_service import OpenAIServiceError
from app.api import chat

# Windows' default ProactorEventLoop has a known bug with asyncpg's SSL
# connections — it hangs and times out. SelectorEventLoop fixes it.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Meesaq.pk API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Global exception handlers: every error returns clear, specific JSON ---

@app.exception_handler(OpenAIServiceError)
async def openai_error_handler(request: Request, exc: OpenAIServiceError):
    logger.error(f"OpenAIServiceError on {request.url.path}: {exc}")
    return JSONResponse(status_code=502, content={"error": str(exc)})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"error": f"Unexpected server error: {type(exc).__name__}: {str(exc)}"},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


app.include_router(chat.router)
