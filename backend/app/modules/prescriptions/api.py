"""
Prescription API

Provides endpoints for:

- Create Prescription
- List Prescriptions
- Get Prescription
- Patient Prescription History
- Update Prescription
- Delete Prescription
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
from app.modules.prescriptions.dependencies import (
    get_prescription_service,
)
from app.modules.prescriptions.schemas import (
    PrescriptionCreate,
    PrescriptionListResponse,
    PrescriptionMessage,
    PrescriptionResponse,
    PrescriptionUpdate,
)
from app.modules.prescriptions.service import (
    PrescriptionService,
)

router = APIRouter(
    prefix="/prescriptions",
    tags=["Prescriptions"],
    dependencies=[Depends(AdminDoctorReception)],
)


# ==========================================================
# Create
# ==========================================================

@router.post(
    "",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_prescription(
    data: PrescriptionCreate,
    current_user: User = Depends(AdminDoctorReception),
    service: PrescriptionService = Depends(
        get_prescription_service,
    ),
):
    prescription = await service.create_prescription(
        data=data,
        created_by=current_user,
    )

    return PrescriptionResponse.model_validate(
        prescription,
    )


# ==========================================================
# List
# ==========================================================

@router.get(
    "",
    response_model=PrescriptionListResponse,
)
async def list_prescriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: PrescriptionService = Depends(
        get_prescription_service,
    ),
):
    return await service.list_prescriptions(
        skip=skip,
        limit=limit,
    )


# ==========================================================
# Patient History
# ==========================================================

@router.get(
    "/patient/{patient_id}",
    response_model=list[PrescriptionResponse],
)
async def patient_prescriptions(
    patient_id: uuid.UUID,
    service: PrescriptionService = Depends(
        get_prescription_service,
    ),
):
    prescriptions = await service.get_patient_prescriptions(
        patient_id,
    )

    return [
        PrescriptionResponse.model_validate(
            prescription,
        )
        for prescription in prescriptions
    ]


# ==========================================================
# Get
# ==========================================================

@router.get(
    "/{prescription_id}",
    response_model=PrescriptionResponse,
)
async def get_prescription(
    prescription_id: uuid.UUID,
    service: PrescriptionService = Depends(
        get_prescription_service,
    ),
):
    prescription = await service.get_prescription(
        prescription_id,
    )

    return PrescriptionResponse.model_validate(
        prescription,
    )


# ==========================================================
# Update
# ==========================================================

@router.put(
    "/{prescription_id}",
    response_model=PrescriptionResponse,
)
async def update_prescription(
    prescription_id: uuid.UUID,
    data: PrescriptionUpdate,
    service: PrescriptionService = Depends(
        get_prescription_service,
    ),
):
    prescription = await service.update_prescription(
        prescription_id=prescription_id,
        data=data,
    )

    return PrescriptionResponse.model_validate(
        prescription,
    )


# ==========================================================
# Delete
# ==========================================================

@router.delete(
    "/{prescription_id}",
    response_model=PrescriptionMessage,
)
async def delete_prescription(
    prescription_id: uuid.UUID,
    service: PrescriptionService = Depends(
        get_prescription_service,
    ),
):
    await service.delete_prescription(
        prescription_id,
    )

    return PrescriptionMessage(
        message="Prescription deleted successfully.",
    )