"""
Prescription Service

Contains all Prescription business logic.
"""

from __future__ import annotations

import uuid

from app.core.exceptions import ResourceNotFoundException
from app.database.unit_of_work import UnitOfWork
from app.modules.auth.models import User
from app.modules.prescriptions.models import (
    Prescription,
    PrescriptionItem,
)
from app.modules.prescriptions.repository import (
    PrescriptionRepository,
)
from app.modules.prescriptions.schemas import (
    PrescriptionCreate,
    PrescriptionListResponse,
    PrescriptionUpdate,
)


class PrescriptionService:
    """
    Prescription business logic.
    """

    def __init__(
        self,
        repository: PrescriptionRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Prescription Number
    # ==========================================================

    async def _generate_prescription_number(
        self,
    ) -> str:

        last_number = (
            await self.repository.get_last_prescription_number()
        )

        if last_number is None:
            return "RX-000001"

        number = int(
            last_number.split("-")[1]
        )

        return f"RX-{number + 1:06d}"

    # ==========================================================
    # Create
    # ==========================================================

    async def create_prescription(
        self,
        *,
        data: PrescriptionCreate,
        created_by: User,
    ) -> Prescription:

        prescription = Prescription(
            prescription_number=await self._generate_prescription_number(),
            medical_record_id=data.medical_record_id,
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            notes=data.notes,
            created_by_id=created_by.id,
        )

        async with self.uow:

            await self.repository.create_prescription(
                prescription,
            )

            for medicine in data.items:

                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    medicine_name=medicine.medicine_name,
                    dosage=medicine.dosage,
                    frequency=medicine.frequency,
                    duration=medicine.duration,
                    route=medicine.route,
                    instructions=medicine.instructions,
                    quantity=medicine.quantity,
                )

                await self.repository.add_item(
                    item,
                )

            await self.repository.refresh(
                prescription,
            )

        return prescription

    # ==========================================================
    # Get
    # ==========================================================

    async def get_prescription(
        self,
        prescription_id: uuid.UUID,
    ) -> Prescription:

        prescription = (
            await self.repository.get_by_uuid(
                prescription_id,
            )
        )

        if (
            prescription is None
            or prescription.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Prescription",
            )

        return prescription

    # ==========================================================
    # List
    # ==========================================================

    async def list_prescriptions(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> PrescriptionListResponse:

        prescriptions = (
            await self.repository.get_paginated(
                skip=skip,
                limit=limit,
            )
        )

        total = (
            await self.repository.total_count()
        )

        return PrescriptionListResponse(
            total=total,
            items=prescriptions,
        )

    # ==========================================================
    # Patient Prescriptions
    # ==========================================================

    async def get_patient_prescriptions(
        self,
        patient_id: uuid.UUID,
    ) -> list[Prescription]:

        return (
            await self.repository.get_by_patient(
                patient_id,
            )
        )

    # ==========================================================
    # Update
    # ==========================================================

    async def update_prescription(
        self,
        *,
        prescription_id: uuid.UUID,
        data: PrescriptionUpdate,
    ) -> Prescription:

        prescription = (
            await self.repository.get_by_uuid(
                prescription_id,
            )
        )

        if (
            prescription is None
            or prescription.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Prescription",
            )

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        async with self.uow:

            prescription = (
                await self.repository.update_prescription(
                    prescription,
                    **update_data,
                )
            )

        return prescription

    # ==========================================================
    # Delete
    # ==========================================================

    async def delete_prescription(
        self,
        prescription_id: uuid.UUID,
    ) -> None:

        prescription = (
            await self.repository.get_by_uuid(
                prescription_id,
            )
        )

        if (
            prescription is None
            or prescription.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Prescription",
            )

        async with self.uow:

            await self.repository.soft_delete(
                prescription,
            )