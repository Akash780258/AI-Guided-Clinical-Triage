from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings

# ==========================================================
# Authentication
# ==========================================================

from app.modules.auth.api import (
    router as auth_router,
)

# ==========================================================
# Patients
# ==========================================================

from app.modules.patients.api import (
    router as patients_router,
)

from app.modules.patients.file_upload import (
    router as patient_file_upload_router,
)

# ==========================================================
# Doctors
# ==========================================================

from app.modules.doctors.api import (
    router as doctors_router,
)

# ==========================================================
# Appointments
# ==========================================================

from app.modules.appointments.api import (
    router as appointments_router,
)

# ==========================================================
# Reception
# ==========================================================

from app.modules.reception import (
    router as reception_router,
)

# ==========================================================
# Medical Records
# ==========================================================

from app.modules.medical_records import (
    router as medical_records_router,
)

# ==========================================================
# Prescriptions
# ==========================================================

from app.modules.prescriptions import (
    router as prescriptions_router,
)

# ==========================================================
# Billing
# ==========================================================

from app.modules.billing import (
    router as billing_router,
)

# ==========================================================
# Pharmacy
# ==========================================================

from app.modules.pharmacy import (
    router as pharmacy_router,
)

# ==========================================================
# Laboratory
# ==========================================================

from app.modules.laboratory import (
    router as laboratory_router,
)

# ==========================================================
# Users
# ==========================================================

from app.modules.users.api import (
    router as users_router,
)

# ==========================================================
# Dashboard
# ==========================================================

from app.modules.dashboard.api import (
    router as dashboard_router,
)

# ==========================================================
# Audit
# ==========================================================

from app.modules.audit.api import (
    router as audit_router,
)

# ==========================================================
# Notifications
# ==========================================================

from app.modules.notifications.api import (
    router as notification_router,
)

# ==========================================================
# Reports
# ==========================================================

from app.modules.reports.api import (
    router as reports_router,
)

# ==========================================================
# Digital Twin
# ==========================================================

from app.modules.digital_twin import (
    router as digital_twin_router,
)

# ==========================================================
# Document Processor
# ==========================================================

from app.modules.document_processor import (
    router as document_processor_router,
)

# ==========================================================
# Document Classifier
# ==========================================================

from app.modules.document_classifier import (
    router as document_classifier_router,
)


# ==========================================================
# Main API Router
# ==========================================================

api_router = APIRouter()


# ==========================================================
# Health
# ==========================================================

@api_router.get(
    "/health",
    tags=["Health"],
)
async def health_check():
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ==========================================================
# Authentication
# ==========================================================

api_router.include_router(
    auth_router,
)


# ==========================================================
# Patients
# ==========================================================

api_router.include_router(
    patients_router,
)


# ==========================================================
# Patient File Upload
# ==========================================================

api_router.include_router(
    patient_file_upload_router,
)


# ==========================================================
# Doctors
# ==========================================================

api_router.include_router(
    doctors_router,
)


# ==========================================================
# Appointments
# ==========================================================

api_router.include_router(
    appointments_router,
)


# ==========================================================
# Reception
# ==========================================================

api_router.include_router(
    reception_router,
)


# ==========================================================
# Medical Records
# ==========================================================

api_router.include_router(
    medical_records_router,
)


# ==========================================================
# Prescriptions
# ==========================================================

api_router.include_router(
    prescriptions_router,
)


# ==========================================================
# Billing
# ==========================================================

api_router.include_router(
    billing_router,
)


# ==========================================================
# Pharmacy
# ==========================================================

api_router.include_router(
    pharmacy_router,
)


# ==========================================================
# Laboratory
# ==========================================================

api_router.include_router(
    laboratory_router,
)


# ==========================================================
# Users
# ==========================================================

api_router.include_router(
    users_router,
)


# ==========================================================
# Dashboard
# ==========================================================

api_router.include_router(
    dashboard_router,
)


# ==========================================================
# Audit
# ==========================================================

api_router.include_router(
    audit_router,
)


# ==========================================================
# Notifications
# ==========================================================

api_router.include_router(
    notification_router,
)


# ==========================================================
# Reports
# ==========================================================

api_router.include_router(
    reports_router,
)


# ==========================================================
# Digital Twin
# ==========================================================

api_router.include_router(
    digital_twin_router,
)


# ==========================================================
# Document Processor
# ==========================================================

api_router.include_router(
    document_processor_router,
)


# ==========================================================
# Document Classifier
# ==========================================================

api_router.include_router(
    document_classifier_router,
)