"""
Billing API

Provides endpoints for:

- Create Billing
- List Billings
- Get Billing
- Patient Billing History
- Update Billing
- Delete Billing
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
from app.modules.billing.dependencies import (
    get_billing_service,
)
from app.modules.billing.schemas import (
    BillingCreate,
    BillingListResponse,
    BillingMessage,
    BillingResponse,
    BillingUpdate,
)
from app.modules.billing.service import (
    BillingService,
)

router = APIRouter(
    prefix="/billing",
    tags=["Billing"],
    dependencies=[Depends(AdminDoctorReception)],
)


# ==========================================================
# Create Billing
# ==========================================================

@router.post(
    "",
    response_model=BillingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_billing(
    data: BillingCreate,
    current_user: User = Depends(AdminDoctorReception),
    service: BillingService = Depends(
        get_billing_service,
    ),
):
    billing = await service.create_billing(
        data=data,
        created_by=current_user,
    )

    return BillingResponse.model_validate(
        billing,
    )


# ==========================================================
# List Billings
# ==========================================================

@router.get(
    "",
    response_model=BillingListResponse,
)
async def list_billings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: BillingService = Depends(
        get_billing_service,
    ),
):
    return await service.list_billings(
        skip=skip,
        limit=limit,
    )


# ==========================================================
# Patient Billing History
# ==========================================================

@router.get(
    "/patient/{patient_id}",
    response_model=list[BillingResponse],
)
async def patient_billings(
    patient_id: uuid.UUID,
    service: BillingService = Depends(
        get_billing_service,
    ),
):
    billings = await service.get_patient_billings(
        patient_id,
    )

    return [
        BillingResponse.model_validate(
            billing,
        )
        for billing in billings
    ]


# ==========================================================
# Get Billing
# ==========================================================

@router.get(
    "/{billing_id}",
    response_model=BillingResponse,
)
async def get_billing(
    billing_id: uuid.UUID,
    service: BillingService = Depends(
        get_billing_service,
    ),
):
    billing = await service.get_billing(
        billing_id,
    )

    return BillingResponse.model_validate(
        billing,
    )


# ==========================================================
# Update Billing
# ==========================================================

@router.put(
    "/{billing_id}",
    response_model=BillingResponse,
)
async def update_billing(
    billing_id: uuid.UUID,
    data: BillingUpdate,
    service: BillingService = Depends(
        get_billing_service,
    ),
):
    billing = await service.update_billing(
        billing_id=billing_id,
        data=data,
    )

    return BillingResponse.model_validate(
        billing,
    )


# ==========================================================
# Delete Billing
# ==========================================================

@router.delete(
    "/{billing_id}",
    response_model=BillingMessage,
)
async def delete_billing(
    billing_id: uuid.UUID,
    service: BillingService = Depends(
        get_billing_service,
    ),
):
    await service.delete_billing(
        billing_id,
    )

    return BillingMessage(
        message="Billing deleted successfully.",
    )