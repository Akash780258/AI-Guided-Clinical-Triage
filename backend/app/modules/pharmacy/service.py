"""
Pharmacy Service

Contains all Pharmacy business logic.
"""

from __future__ import annotations

import uuid

from app.core.exceptions import (
    ConflictException,
    ResourceNotFoundException,
)
from app.database.unit_of_work import UnitOfWork
from app.modules.auth.models import User
from app.modules.pharmacy.models import Medicine
from app.modules.pharmacy.repository import PharmacyRepository
from app.modules.pharmacy.schemas import (
    MedicineCreate,
    MedicineListResponse,
    MedicineUpdate,
)


class PharmacyService:
    """
    Pharmacy business logic.
    """

    def __init__(
        self,
        repository: PharmacyRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Medicine Code
    # ==========================================================

    async def _generate_medicine_code(
        self,
    ) -> str:

        last_code = await self.repository.get_last_medicine_code()

        if last_code is None:
            return "MED-000001"

        number = int(
            last_code.split("-")[1]
        )

        return f"MED-{number + 1:06d}"

    # ==========================================================
    # Create
    # ==========================================================

    async def create_medicine(
        self,
        *,
        data: MedicineCreate,
        created_by: User,
    ) -> Medicine:

        medicine = Medicine(
            medicine_code=await self._generate_medicine_code(),
            name=data.name,
            generic_name=data.generic_name,
            manufacturer=data.manufacturer,
            category=data.category,
            strength=data.strength,
            dosage_form=data.dosage_form,
            unit_price=data.unit_price,
            stock_quantity=data.stock_quantity,
            minimum_stock=data.minimum_stock,
            expiry_date=data.expiry_date,
            batch_number=data.batch_number,
            created_by_id=created_by.id,
        )

        async with self.uow:

            await self.repository.create_medicine(
                medicine,
            )

        return medicine

    # ==========================================================
    # Get
    # ==========================================================

    async def get_medicine(
        self,
        medicine_id: uuid.UUID,
    ) -> Medicine:

        medicine = await self.repository.get_by_uuid(
            medicine_id,
        )

        if (
            medicine is None
            or medicine.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Medicine",
            )

        return medicine

    # ==========================================================
    # List
    # ==========================================================

    async def list_medicines(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> MedicineListResponse:

        medicines = await self.repository.get_paginated(
            skip=skip,
            limit=limit,
        )

        total = await self.repository.total_count()

        return MedicineListResponse(
            total=total,
            items=medicines,
        )

    # ==========================================================
    # Search
    # ==========================================================

    async def search_medicines(
        self,
        *,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> MedicineListResponse:

        medicines = await self.repository.search(
            query=query,
            skip=skip,
            limit=limit,
        )

        return MedicineListResponse(
            total=len(medicines),
            items=medicines,
        )

    # ==========================================================
    # Update
    # ==========================================================

    async def update_medicine(
        self,
        *,
        medicine_id: uuid.UUID,
        data: MedicineUpdate,
    ) -> Medicine:

        medicine = await self.repository.get_by_uuid(
            medicine_id,
        )

        if (
            medicine is None
            or medicine.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Medicine",
            )

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        async with self.uow:

            medicine = await self.repository.update_medicine(
                medicine,
                **update_data,
            )

        return medicine

    # ==========================================================
    # Delete
    # ==========================================================

    async def delete_medicine(
        self,
        medicine_id: uuid.UUID,
    ) -> None:

        medicine = await self.repository.get_by_uuid(
            medicine_id,
        )

        if (
            medicine is None
            or medicine.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Medicine",
            )

        async with self.uow:

            await self.repository.soft_delete(
                medicine,
            )