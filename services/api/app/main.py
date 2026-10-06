"""
ResQGrid AI — FastAPI Application Entry Point

Intelligent Emergency Resource Network
AI recommends. Humans approve. Every important decision is explainable and auditable.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import engine
from app.middleware.request_id import RequestIDMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("ResQGrid AI starting up", env=settings.APP_ENV)
    # Verify database connection on startup
    try:
        async with engine.begin() as conn:
            logger.info("Database connection verified")
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Static uploads (evidence images) ----
import os
_uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
if os.path.exists(_uploads_dir):
    app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")

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
