"""
Security package.
"""

from app.core.security.permissions import (
    AdminDoctorReception,
    AdminOnly,
    AdminOrDoctor,
    AdminOrReception,
    DoctorOnly,
    LaboratoryOnly,
    PharmacyOnly,
    ReceptionOnly,
    ResearchOnly,
    require_roles,
)

__all__ = [
    "require_roles",
    "AdminOnly",
    "DoctorOnly",
    "ReceptionOnly",
    "PharmacyOnly",
    "LaboratoryOnly",
    "ResearchOnly",
    "AdminOrDoctor",
    "AdminOrReception",
    "AdminDoctorReception",
]