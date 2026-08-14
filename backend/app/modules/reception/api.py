"""
Reception API

Reception workflow endpoints.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import (
    APIRouter,
    Depends,
)

from app.core.security import AdminDoctorReception
from app.modules.reception.dependencies import (
    get_reception_service,
)
from app.modules.reception.schemas import (
    QueueResponse,
    ReceptionMessage,
)
from app.modules.reception.service import (
    ReceptionService,
)

router = APIRouter(
    prefix="/reception",
    tags=["Reception"],
    dependencies=[Depends(AdminDoctorReception)],
)


# ==========================================================
# Today's Queue
# ==========================================================

@router.get(
    "/queue/today",
    response_model=QueueResponse,
)
async def today_queue(
    appointment_date: date,
    service: ReceptionService = Depends(
        get_reception_service,
    ),
):
    return await service.get_today_queue(
        appointment_date,
    )


# ==========================================================
# Waiting Queue
# ==========================================================

@router.get(
    "/queue/waiting",
    response_model=QueueResponse,
)
async def waiting_queue(
    appointment_date: date,
    service: ReceptionService = Depends(
        get_reception_service,
    ),
):
    return await service.get_waiting_queue(
        appointment_date,
    )


# ==========================================================
# Check-In
# ==========================================================

@router.patch(
    "/{appointment_id}/check-in",
    response_model=ReceptionMessage,
)
async def check_in(
    appointment_id: uuid.UUID,
    service: ReceptionService = Depends(
        get_reception_service,
    ),
):
    await service.check_in(
        appointment_id,
    )

    return ReceptionMessage(
        message="Patient checked in successfully.",
    )


# ==========================================================
# Mark Waiting
# ==========================================================

@router.patch(
    "/{appointment_id}/waiting",
    response_model=ReceptionMessage,
)
async def mark_waiting(
    appointment_id: uuid.UUID,
    service: ReceptionService = Depends(
        get_reception_service,
    ),
):
    await service.mark_waiting(
        appointment_id,
    )

    return ReceptionMessage(
        message="Patient moved to waiting queue.",
    )


# ==========================================================
# Complete Appointment
# ==========================================================

@router.patch(
    "/{appointment_id}/complete",
    response_model=ReceptionMessage,
)
async def complete(
    appointment_id: uuid.UUID,
    service: ReceptionService = Depends(
        get_reception_service,
    ),
):
    await service.complete(
        appointment_id,
    )

    return ReceptionMessage(
        message="Appointment completed successfully.",
    )