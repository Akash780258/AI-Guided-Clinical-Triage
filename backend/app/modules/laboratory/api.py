"""
Laboratory API
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.security import AdminDoctorReception
from app.modules.auth.models import User
from app.modules.laboratory.dependencies import get_laboratory_service
from app.modules.laboratory.schemas import (
    LaboratoryMessage,
    LabResultCreate,
    LabResultResponse,
    LabTestCreate,
    LabTestListResponse,
    LabTestResponse,
    LabTestUpdate,
)
from app.modules.laboratory.service import LaboratoryService

router = APIRouter(
    prefix="/laboratory",
    tags=["Laboratory"],
    dependencies=[Depends(AdminDoctorReception)],
)


# ==========================================================
# Create Test
# ==========================================================

@router.post(
    "",
    response_model=LabTestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_lab_test(
    data: LabTestCreate,
    current_user: User = Depends(AdminDoctorReception),
    service: LaboratoryService = Depends(
        get_laboratory_service,
    ),
):
    test = await service.create_test(
        data=data,
        created_by=current_user,
    )

    return LabTestResponse.model_validate(test)


# ==========================================================
# List
# ==========================================================

@router.get(
    "",
    response_model=LabTestListResponse,
)
async def list_lab_tests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: LaboratoryService = Depends(
        get_laboratory_service,
    ),
):
    return await service.list_tests(
        skip,
        limit,
    )


# ==========================================================
# Get
# ==========================================================

@router.get(
    "/{test_id}",
    response_model=LabTestResponse,
)
async def get_lab_test(
    test_id: uuid.UUID,
    service: LaboratoryService = Depends(
        get_laboratory_service,
    ),
):
    test = await service.get_test(
        test_id,
    )

    return LabTestResponse.model_validate(
        test,
    )


# ==========================================================
# Update
# ==========================================================

@router.put(
    "/{test_id}",
    response_model=LabTestResponse,
)
async def update_lab_test(
    test_id: uuid.UUID,
    data: LabTestUpdate,
    service: LaboratoryService = Depends(
        get_laboratory_service,
    ),
):
    test = await service.update_test(
        test_id=test_id,
        data=data,
    )

    return LabTestResponse.model_validate(
        test,
    )


# ==========================================================
# Create Result
# ==========================================================

@router.post(
    "/result",
    response_model=LabResultResponse,
)
async def create_lab_result(
    data: LabResultCreate,
    service: LaboratoryService = Depends(
        get_laboratory_service,
    ),
):
    return await service.create_result(
        data,
    )


# ==========================================================
# Delete
# ==========================================================

@router.delete(
    "/{test_id}",
    response_model=LaboratoryMessage,
)
async def delete_lab_test(
    test_id: uuid.UUID,
    service: LaboratoryService = Depends(
        get_laboratory_service,
    ),
):
    await service.delete_test(
        test_id,
    )

    return LaboratoryMessage(
        message="Laboratory test deleted successfully.",
    )