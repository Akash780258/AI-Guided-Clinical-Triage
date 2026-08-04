from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings
from app.modules.auth.api import router as auth_router
from app.modules.patients.api import router as patients_router
from app.modules.doctors.api import router as doctors_router

api_router = APIRouter()


# ==========================================================
# Health
# ==========================================================

@api_router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ==========================================================
# Routers
# ==========================================================

api_router.include_router(auth_router)
api_router.include_router(patients_router)
api_router.include_router(doctors_router)