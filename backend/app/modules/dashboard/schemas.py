from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    active_patients: int
    appointments_today: int
    doctors_available: int
    critical_alerts: int
    pending_reports: int
    revenue_today: float