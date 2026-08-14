"""
Pharmacy API

Provides endpoints for:

- Create Medicine
- List Medicines
- Search Medicines
- Get Medicine
- Update Medicine
- Delete Medicine
"""

from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.pharmacy.dependencies import (
    get_pharmacy_service,
)
from app.modules.pharmacy.schemas import (
    MedicineCreate,
    MedicineListResponse,
    MedicineMessage,
    MedicineResponse,
    MedicineUpdate,
)
from app.modules.pharmacy.service import (
    PharmacyService,
)

router = APIRouter(
    prefix="/pharmacy",
    tags=["Pharmacy"],
)


# ==========================================================
# Create Medicine
# ==========================================================

@router.post(
    "",
    response_model=MedicineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medicine(
    data: MedicineCreate,
    current_user: User = Depends(get_current_user),
    service: PharmacyService = Depends(
        get_pharmacy_service,
    ),
):
    medicine = await service.create_medicine(
        data=data,
        created_by=current_user,
    )

    return MedicineResponse.model_validate(
        medicine,
    )


# ==========================================================
# List Medicines
# ==========================================================

@router.get(
    "",
    response_model=MedicineListResponse,
)
async def list_medicines(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: PharmacyService = Depends(
        get_pharmacy_service,
    ),
):
    return await service.list_medicines(
        skip=skip,
        limit=limit,
    )


# ==========================================================
# Search Medicines
# ==========================================================

@router.get(
    "/search",
    response_model=MedicineListResponse,
)
async def search_medicines(
    query: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: PharmacyService = Depends(
        get_pharmacy_service,
    ),
):
    return await service.search_medicines(
        query=query,
        skip=skip,
        limit=limit,
    )


# ==========================================================
# Get Medicine
# ==========================================================

@router.get(
    "/{medicine_id}",
    response_model=MedicineResponse,
)
async def get_medicine(
    medicine_id: uuid.UUID,
    service: PharmacyService = Depends(
        get_pharmacy_service,
    ),
):
    medicine = await service.get_medicine(
        medicine_id,
    )

    return MedicineResponse.model_validate(
        medicine,
    )


# ==========================================================
# Update Medicine
# ==========================================================

@router.put(
    "/{medicine_id}",
    response_model=MedicineResponse,
)
async def update_medicine(
    medicine_id: uuid.UUID,
    data: MedicineUpdate,
    service: PharmacyService = Depends(
        get_pharmacy_service,
    ),
):
    medicine = await service.update_medicine(
        medicine_id=medicine_id,
        data=data,
    )

    return MedicineResponse.model_validate(
        medicine,
    )


# ==========================================================
# Delete Medicine
# ==========================================================

@router.delete(
    "/{medicine_id}",
    response_model=MedicineMessage,
)
async def delete_medicine(
    medicine_id: uuid.UUID,
    service: PharmacyService = Depends(
        get_pharmacy_service,
    ),
):
    await service.delete_medicine(
        medicine_id,
    )

    return MedicineMessage(
        message="Medicine deleted successfully.",
    )