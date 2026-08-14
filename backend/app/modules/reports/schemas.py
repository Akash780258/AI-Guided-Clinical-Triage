"""
Report Schemas
"""

from __future__ import annotations

from pydantic import BaseModel


class DashboardReport(BaseModel):
    total_patients: int
    total_doctors: int
    total_appointments: int
    total_prescriptions: int
    total_bills: int
    total_revenue: float