"""
Billing Service

Contains all Billing business logic.
"""

from __future__ import annotations

import uuid

from app.core.exceptions import ResourceNotFoundException
from app.database.unit_of_work import UnitOfWork
from app.modules.auth.models import User
from app.modules.billing.models import (
    Billing,
    BillingStatus,
)
from app.modules.billing.repository import (
    BillingRepository,
)
from app.modules.billing.schemas import (
    BillingCreate,
    BillingListResponse,
    BillingUpdate,
)


class BillingService:
    """
    Billing business logic.
    """

    def __init__(
        self,
        repository: BillingRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Bill Number
    # ==========================================================

    async def _generate_bill_number(
        self,
    ) -> str:

        last_bill = await self.repository.get_last_bill_number()

        if last_bill is None:
            return "BILL-000001"

        number = int(
            last_bill.split("-")[1]
        )

        return f"BILL-{number + 1:06d}"

    # ==========================================================
    # Create
    # ==========================================================

    async def create_billing(
        self,
        *,
        data: BillingCreate,
        created_by: User,
    ) -> Billing:

        total = (
            data.subtotal
            + data.tax
            - data.discount
        )

        billing = Billing(
            bill_number=await self._generate_bill_number(),
            patient_id=data.patient_id,
            appointment_id=data.appointment_id,
            subtotal=data.subtotal,
            tax=data.tax,
            discount=data.discount,
            total=total,
            payment_method=data.payment_method,
            notes=data.notes,
            status=BillingStatus.PENDING,
            created_by_id=created_by.id,
        )

        async with self.uow:

            await self.repository.create_billing(
                billing,
            )

        return billing

    # ==========================================================
    # Get
    # ==========================================================

    async def get_billing(
        self,
        billing_id: uuid.UUID,
    ) -> Billing:

        billing = await self.repository.get_by_uuid(
            billing_id,
        )

        if (
            billing is None
            or billing.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Billing",
            )

        return billing

    # ==========================================================
    # List
    # ==========================================================

    async def list_billings(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> BillingListResponse:

        billings = await self.repository.get_paginated(
            skip=skip,
            limit=limit,
        )

        total = await self.repository.total_count()

        return BillingListResponse(
            total=total,
            items=billings,
        )

    # ==========================================================
    # Patient Bills
    # ==========================================================

    async def get_patient_billings(
        self,
        patient_id: uuid.UUID,
    ) -> list[Billing]:

        return await self.repository.get_by_patient(
            patient_id,
        )

    # ==========================================================
    # Update
    # ==========================================================

    async def update_billing(
        self,
        *,
        billing_id: uuid.UUID,
        data: BillingUpdate,
    ) -> Billing:

        billing = await self.repository.get_by_uuid(
            billing_id,
        )

        if (
            billing is None
            or billing.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Billing",
            )

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        subtotal = update_data.get(
            "subtotal",
            billing.subtotal,
        )

        tax = update_data.get(
            "tax",
            billing.tax,
        )

        discount = update_data.get(
            "discount",
            billing.discount,
        )

        update_data["total"] = (
            subtotal
            + tax
            - discount
        )

        async with self.uow:

            billing = await self.repository.update_billing(
                billing,
                **update_data,
            )

        return billing

    # ==========================================================
    # Delete
    # ==========================================================

    async def delete_billing(
        self,
        billing_id: uuid.UUID,
    ) -> None:

        billing = await self.repository.get_by_uuid(
            billing_id,
        )

        if (
            billing is None
            or billing.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Billing",
            )

        async with self.uow:

            await self.repository.soft_delete(
                billing,
            )