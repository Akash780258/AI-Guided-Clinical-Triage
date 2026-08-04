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

# ==========================================================
# Doctors
# ==========================================================

from app.modules.doctors.models import Doctor

# ==========================================================
# Future Modules
# ==========================================================

# from app.modules.appointments.models import Appointment
# from app.modules.medical_records.models import MedicalRecord
# from app.modules.prescriptions.models import Prescription
# from app.modules.lab.models import LabResult
# from app.modules.ai.models import ClinicalTwin

__all__ = [
    "User",
    "Patient",
    "Doctor",
]