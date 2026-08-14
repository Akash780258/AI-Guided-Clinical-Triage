"""
Dashboard Schemas

Response models for all dashboard endpoints.
"""

from pydantic import BaseModel


# ==========================================================
# Admin Dashboard
# ==========================================================

class AdminDashboardResponse(BaseModel):
    total_patients: int
    total_doctors: int
    total_appointments: int
    today_appointments: int
    pending_lab_tests: int
    active_prescriptions: int
    pending_bills: int
    total_revenue: float


# ==========================================================
# Doctor Dashboard
# ==========================================================

class DoctorDashboardResponse(BaseModel):
    today_appointments: int
    total_patients: int
    pending_lab_results: int
    active_prescriptions: int


# ==========================================================
# Reception Dashboard
# ==========================================================

class ReceptionDashboardResponse(BaseModel):
    today_queue: int
    waiting: int
    completed: int


# ==========================================================
# Laboratory Dashboard
# ==========================================================

class LaboratoryDashboardResponse(BaseModel):
    pending_tests: int
    completed_today: int


# ==========================================================
# Billing Dashboard
# ==========================================================

class BillingDashboardResponse(BaseModel):
    pending_bills: int
    paid_bills: int
    total_revenue: float