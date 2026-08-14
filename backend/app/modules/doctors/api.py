"""
Doctor API

Provides endpoints for:

- Create Doctor
- List Doctors
- Search Doctors
- Get Doctor
- Update Doctor
- Delete Doctor
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.security import (
    AdminDoctorReception,
    AdminOnly,
)
from app.modules.auth.models import User
from app.modules.doctors.dependencies import get_doctor_service
from app.modules.doctors.schemas import (
    DoctorCreate,
    DoctorListResponse,
    DoctorMessage,
    DoctorResponse,
    DoctorUpdate,
)
from app.modules.doctors.service import DoctorService


router = APIRouter(
    prefix="/doctors",
    tags=["Doctors"],
)


# ==========================================================
# Create Doctor
# ADMIN ONLY
# ==========================================================

@router.post(
    "",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_doctor(
    data: DoctorCreate,
    current_user: User = Depends(AdminOnly),
    service: DoctorService = Depends(
        get_doctor_service,
    ),
):
    doctor = await service.create_doctor(
        data=data,
        created_by=current_user,
    )

    return DoctorResponse.model_validate(
        doctor,
    )


# ==========================================================
# List Doctors
# ADMIN / DOCTOR / RECEPTIONIST
# ==========================================================

@router.get(
    "",
    response_model=DoctorListResponse,
)
async def list_doctors(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(
        AdminDoctorReception,
    ),
    service: DoctorService = Depends(
        get_doctor_service,
    ),
):
    return await service.list_doctors(
        skip=skip,
        limit=limit,
    )


# ==========================================================
# Search Doctors
# ADMIN / DOCTOR / RECEPTIONIST
# ==========================================================

@router.get(
    "/search",
    response_model=DoctorListResponse,
)
async def search_doctors(
    query: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(
        AdminDoctorReception,
    ),
    service: DoctorService = Depends(
        get_doctor_service,
    ),
):
    return await service.search_doctors(
        query=query,
        skip=skip,
        limit=limit,
    )


# ==========================================================
# Get Doctor
# ADMIN / DOCTOR / RECEPTIONIST
# ==========================================================

@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
)
async def get_doctor(
    doctor_id: uuid.UUID,
    current_user: User = Depends(
        AdminDoctorReception,
    ),
    service: DoctorService = Depends(
        get_doctor_service,
    ),
):
    doctor = await service.get_doctor(
        doctor_id,
    )

    return DoctorResponse.model_validate(
        doctor,
    )


# ==========================================================
# Update Doctor
# ADMIN ONLY
# ==========================================================

@router.put(
    "/{doctor_id}",
    response_model=DoctorResponse,
)
async def update_doctor(
    doctor_id: uuid.UUID,
    data: DoctorUpdate,
    current_user: User = Depends(AdminOnly),
    service: DoctorService = Depends(
        get_doctor_service,
    ),
):
    doctor = await service.update_doctor(
        doctor_id=doctor_id,
        data=data,
    )

    return DoctorResponse.model_validate(
        doctor,
    )


# ==========================================================
# Delete Doctor
# ADMIN ONLY
# ==========================================================

@router.delete(
    "/{doctor_id}",
    response_model=DoctorMessage,
)
async def delete_doctor(
    doctor_id: uuid.UUID,
    current_user: User = Depends(AdminOnly),
    service: DoctorService = Depends(
        get_doctor_service,
    ),
):
    await service.delete_doctor(
        doctor_id,
    )

    return DoctorMessage(
        message="Doctor deleted successfully.",
    )