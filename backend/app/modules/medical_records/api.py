"""
Medical Record API

Provides endpoints for:

- Create Medical Record
- List Medical Records
- Get Medical Record
- Update Medical Record
- Delete Medical Record
- Patient Medical History
"""

from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from app.core.security import AdminDoctorReception
from app.modules.auth.models import User
from app.modules.medical_records.dependencies import (
    get_medical_record_service,
)
from app.modules.medical_records.schemas import (
    MedicalRecordCreate,
    MedicalRecordListResponse,
    MedicalRecordMessage,
    MedicalRecordResponse,
    MedicalRecordUpdate,
)
from app.modules.medical_records.service import (
    MedicalRecordService,
)

router = APIRouter(
    prefix="/medical-records",
    tags=["Medical Records"],
    dependencies=[Depends(AdminDoctorReception)],
)


# ==========================================================
# Create
# ==========================================================

@router.post(
    "",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medical_record(
    data: MedicalRecordCreate,
    current_user: User = Depends(AdminDoctorReception),
    service: MedicalRecordService = Depends(
        get_medical_record_service,
    ),
):
    record = await service.create_record(
        data=data,
        created_by=current_user,
    )

    return MedicalRecordResponse.model_validate(
        record,
    )


# ==========================================================
# List
# ==========================================================

@router.get(
    "",
    response_model=MedicalRecordListResponse,
)
async def list_medical_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: MedicalRecordService = Depends(
        get_medical_record_service,
    ),
):
    return await service.list_records(
        skip=skip,
        limit=limit,
    )


# ==========================================================
# Patient History
# ==========================================================

@router.get(
    "/patient/{patient_id}",
    response_model=list[MedicalRecordResponse],
)
async def patient_history(
    patient_id: uuid.UUID,
    service: MedicalRecordService = Depends(
        get_medical_record_service,
    ),
):
    records = await service.get_patient_records(
        patient_id,
    )

    return [
        MedicalRecordResponse.model_validate(record)
        for record in records
    ]


# ==========================================================
# Get
# ==========================================================

@router.get(
    "/{record_id}",
    response_model=MedicalRecordResponse,
)
async def get_medical_record(
    record_id: uuid.UUID,
    service: MedicalRecordService = Depends(
        get_medical_record_service,
    ),
):
    record = await service.get_record(
        record_id,
    )

    return MedicalRecordResponse.model_validate(
        record,
    )


# ==========================================================
# Update
# ==========================================================

@router.put(
    "/{record_id}",
    response_model=MedicalRecordResponse,
)
async def update_medical_record(
    record_id: uuid.UUID,
    data: MedicalRecordUpdate,
    service: MedicalRecordService = Depends(
        get_medical_record_service,
    ),
):
    record = await service.update_record(
        record_id=record_id,
        data=data,
    )

    return MedicalRecordResponse.model_validate(
        record,
    )


# ==========================================================
# Delete
# ==========================================================

@router.delete(
    "/{record_id}",
    response_model=MedicalRecordMessage,
)
async def delete_medical_record(
    record_id: uuid.UUID,
    service: MedicalRecordService = Depends(
        get_medical_record_service,
    ),
):
    await service.delete_record(
        record_id,
    )

    return MedicalRecordMessage(
        message="Medical record deleted successfully.",
    )