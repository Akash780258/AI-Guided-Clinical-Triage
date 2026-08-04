"""
AGCT Backend Entry Point

Initializes:

- FastAPI
- Logging
- Middleware
- Lifespan
- API Routers
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logger import configure_logging, get_logger
from app.core.exception_handlers import register_exception_handlers

# ---------------------------------------------------------
# Configure Logging
# ---------------------------------------------------------

configure_logging()

logger = get_logger(__name__)


# ---------------------------------------------------------
# Lifespan
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    """

    logger.info(
        "Starting AGCT Backend",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )

    yield

    logger.info("Stopping AGCT Backend")


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
register_exception_handlers(app)


# ---------------------------------------------------------
# Middleware
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------

app.include_router(api_router, prefix="/api/v1")


# ---------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    """

    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
    }