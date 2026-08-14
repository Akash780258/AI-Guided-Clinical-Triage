"""
Patient API

Provides endpoints for:

- Create Patient
- List Patients
- Search Patients
- Get Patient
- Update Patient
- Delete Patient
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.security import AdminDoctorReception
from app.modules.auth.models import User
from app.modules.patients.dependencies import get_patient_service
from app.modules.patients.schemas import (
    PatientCreate,
    PatientListResponse,
    PatientMessage,
    PatientResponse,
    PatientUpdate,
)
from app.modules.patients.service import PatientService
from app.modules.patients.file_upload import router as file_upload_router

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
    dependencies=[Depends(AdminDoctorReception)],
)
router.include_router(file_upload_router)


# ==========================================================
# Create
# ==========================================================

@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_patient(
    data: PatientCreate,
    current_user: User = Depends(AdminDoctorReception),
    service: PatientService = Depends(get_patient_service),
):
    patient = await service.create_patient(
        data=data,
        created_by=current_user,
    )

    return PatientResponse.model_validate(patient)


# ==========================================================
# List
# ==========================================================

@router.get(
    "",
    response_model=PatientListResponse,
)
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: PatientService = Depends(get_patient_service),
):
    return await service.list_patients(
        skip=skip,
        limit=limit,
    )


# ==========================================================
# Search
# ==========================================================

@router.get(
    "/search",
    response_model=PatientListResponse,
)
async def search_patients(
    query: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: PatientService = Depends(get_patient_service),
):
    return await service.search_patients(
        query=query,
        skip=skip,
        limit=limit,
    )


# ==========================================================
# Get
# ==========================================================

@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
)
async def get_patient(
    patient_id: uuid.UUID,
    service: PatientService = Depends(get_patient_service),
):
    patient = await service.get_patient(
        patient_id,
    )

    return PatientResponse.model_validate(patient)


# ==========================================================
# Update
# ==========================================================

@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
)
async def update_patient(
    patient_id: uuid.UUID,
    data: PatientUpdate,
    service: PatientService = Depends(get_patient_service),
):
    patient = await service.update_patient(
        patient_id=patient_id,
        data=data,
    )

    return PatientResponse.model_validate(patient)


# ==========================================================
# Delete
# ==========================================================

@router.delete(
    "/{patient_id}",
    response_model=PatientMessage,
)
async def delete_patient(
    patient_id: uuid.UUID,
    service: PatientService = Depends(get_patient_service),
):
    await service.delete_patient(
        patient_id,
    )

    return PatientMessage(
        message="Patient deleted successfully."
    )