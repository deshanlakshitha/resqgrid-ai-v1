"""
ResQGrid AI — FastAPI Application Entry Point

Intelligent Emergency Resource Network
AI recommends. Humans approve. Every important decision is explainable and auditable.
"""

from contextlib import asynccontextmanager
import logging

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import engine
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security import SecurityMiddleware, SECURITY_HEADERS


def configure_logging() -> None:
    """Structured logging: JSON when LOG_FORMAT=json, console otherwise.
    The request ID middleware binds request_id into every log record."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(message)s")
    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


configure_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("ResQGrid AI starting up", env=settings.APP_ENV)
    # Verify database connection on startup
    try:
        async with engine.begin() as conn:
            logger.info("Database connection verified")
    except Exception:
        logger.error("Database connection failed")
    yield
    await engine.dispose()
    logger.info("ResQGrid AI shutting down")


app = FastAPI(
    title="ResQGrid AI",
    description="Intelligent Emergency Resource Network — API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---- Middleware ----
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    logger.error("Unhandled API error", error_type=type(exc).__name__)
    return JSONResponse(
        status_code=500, content={"detail": "An internal error occurred"},
        headers={**SECURITY_HEADERS, "Cache-Control": "no-store"},
    )

# ---- Routes ----
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "service": "resqgrid-ai", "version": "0.1.0"}


@app.get("/", tags=["root"])
async def root():
    """API root — redirect to documentation."""
    return {
        "name": "ResQGrid AI API",
        "version": "0.1.0",
        "docs": "/docs",
        "api": "/api/v1",
    }
