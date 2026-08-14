"""
Appointment API

Provides endpoints for:

- Create Appointment
- List Appointments
- Get Appointment
- Update Appointment
- Cancel Appointment
- Delete Appointment
- Today's Appointments
- Doctor Appointments
- Patient Appointments
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status

from app.core.security import AdminDoctorReception
from app.modules.auth.models import User
from app.modules.appointments.dependencies import (
    get_appointment_service,
)
from app.modules.appointments.schemas import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentMessage,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.modules.appointments.service import (
    AppointmentService,
)

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
    dependencies=[Depends(AdminDoctorReception)],
)


# ==========================================================
# Create
# ==========================================================

@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(AdminDoctorReception),
    service: AppointmentService = Depends(
        get_appointment_service,
    ),
):
    appointment = await service.create_appointment(
        data=data,
        created_by=current_user,
    )

    return AppointmentResponse.model_validate(
        appointment,
    )


# ==========================================================
# List
# ==========================================================

@router.get(
    "",
    response_model=AppointmentListResponse,
)
async def list_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: AppointmentService = Depends(
        get_appointment_service,
    ),
):
    return await service.list_appointments(
        skip=skip,
        limit=limit,
    )


# ==========================================================
# Get
# ==========================================================

@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
)
async def get_appointment(
    appointment_id: uuid.UUID,
    service: AppointmentService = Depends(
        get_appointment_service,
    ),
):
    appointment = await service.get_appointment(
        appointment_id,
    )

    return AppointmentResponse.model_validate(
        appointment,
    )


# ==========================================================
# Update
# ==========================================================

@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse,
)
async def update_appointment(
    appointment_id: uuid.UUID,
    data: AppointmentUpdate,
    service: AppointmentService = Depends(
        get_appointment_service,
    ),
):
    appointment = await service.update_appointment(
        appointment_id=appointment_id,
        data=data,
    )

    return AppointmentResponse.model_validate(
        appointment,
    )


# ==========================================================
# Cancel
# ==========================================================

@router.patch(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    service: AppointmentService = Depends(
        get_appointment_service,
    ),
):
    appointment = await service.cancel_appointment(
        appointment_id,
    )

    return AppointmentResponse.model_validate(
        appointment,
    )


# ==========================================================
# Delete
# ==========================================================

@router.delete(
    "/{appointment_id}",
    response_model=AppointmentMessage,
)
async def delete_appointment(
    appointment_id: uuid.UUID,
    service: AppointmentService = Depends(
        get_appointment_service,
    ),
):
    await service.delete_appointment(
        appointment_id,
    )

    return AppointmentMessage(
        message="Appointment deleted successfully.",
    )


# ==========================================================
# Today's Appointments
# ==========================================================

@router.get(
    "/today",
    response_model=AppointmentListResponse,
)
async def today_appointments(
    appointment_date: date,
    service: AppointmentService = Depends(
        get_appointment_service,
    ),
):
    return await service.list_today(
        appointment_date,
    )


# ==========================================================
# Doctor Appointments
# ==========================================================

@router.get(
    "/doctor/{doctor_id}",
    response_model=AppointmentListResponse,
)
async def doctor_appointments(
    doctor_id: uuid.UUID,
    service: AppointmentService = Depends(
        get_appointment_service,
    ),
):
    return await service.list_by_doctor(
        doctor_id,
    )


# ==========================================================
# Patient Appointments
# ==========================================================

@router.get(
    "/patient/{patient_id}",
    response_model=AppointmentListResponse,
)
async def patient_appointments(
    patient_id: uuid.UUID,
    service: AppointmentService = Depends(
        get_appointment_service,
    ),
):
    return await service.list_by_patient(
        patient_id,
    )