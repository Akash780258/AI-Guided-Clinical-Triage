"""
Database Models

Imports all SQLAlchemy ORM models so they are registered
with Base.metadata.

Alembic imports this module before generating migrations.
Whenever a new model is added, import it here.
"""

# ==========================================================
# Authentication
# ==========================================================

from app.modules.auth.models import User

# ==========================================================
# Patients
# ==========================================================

from app.modules.patients.models import Patient
from app.modules.patients.documents import PatientDocument

# ==========================================================
# Doctors
# ==========================================================

from app.modules.doctors.models import Doctor

# ==========================================================
# Appointments
# ==========================================================

from app.modules.appointments.models import Appointment

# ==========================================================
# Medical Records
# ==========================================================

from app.modules.medical_records.models import MedicalRecord

# ==========================================================
# Prescriptions
# ==========================================================

from app.modules.prescriptions.models import (
    Prescription,
    PrescriptionItem,
)

# ==========================================================
# Billing
# ==========================================================

from app.modules.billing.models import Billing

# ==========================================================
# Pharmacy
# ==========================================================

from app.modules.pharmacy.models import Medicine

# ==========================================================
# Laboratory
# ==========================================================

from app.modules.laboratory.models import (
    LabResult,
    LabTest,
)

# ==========================================================
# Audit
# ==========================================================

from app.modules.audit.models import AuditLog

# ==========================================================
# Notifications
# ==========================================================

from app.modules.notifications.models import Notification


__all__ = [
    "User",
    "Patient",
    "PatientDocument",
    "Doctor",
    "Appointment",
    "MedicalRecord",
    "Prescription",
    "PrescriptionItem",
    "Billing",
    "Medicine",
    "LabTest",
    "LabResult",
    "AuditLog",
    "Notification",
]