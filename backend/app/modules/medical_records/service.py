"""
Medical Record Service

Contains all Medical Record business logic.
"""

from __future__ import annotations

import uuid

from app.core.exceptions import ResourceNotFoundException
from app.database.unit_of_work import UnitOfWork
from app.modules.auth.models import User
from app.modules.medical_records.models import MedicalRecord
from app.modules.medical_records.repository import (
    MedicalRecordRepository,
)
from app.modules.medical_records.schemas import (
    MedicalRecordCreate,
    MedicalRecordListResponse,
    MedicalRecordUpdate,
)


class MedicalRecordService:
    """
    Medical Record business logic.
    """

    def __init__(
        self,
        repository: MedicalRecordRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Record Number
    # ==========================================================

    async def _generate_record_number(
        self,
    ) -> str:

        last_record_number = (
            await self.repository.get_last_record_number()
        )

        if last_record_number is None:
            return "MR-000001"

        last_number = int(
            last_record_number.split("-")[1]
        )

        return f"MR-{last_number + 1:06d}"

    # ==========================================================
    # Create
    # ==========================================================

    async def create_record(
        self,
        *,
        data: MedicalRecordCreate,
        created_by: User,
    ) -> MedicalRecord:

        record = MedicalRecord(
            record_number=await self._generate_record_number(),
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            appointment_id=data.appointment_id,
            chief_complaint=data.chief_complaint,
            history_present_illness=data.history_present_illness,
            past_medical_history=data.past_medical_history,
            family_history=data.family_history,
            allergies=data.allergies,
            current_medications=data.current_medications,
            physical_examination=data.physical_examination,
            diagnosis=data.diagnosis,
            treatment_plan=data.treatment_plan,
            notes=data.notes,
            created_by_id=created_by.id,
        )

        async with self.uow:

            await self.repository.create_record(
                record,
            )

        return record

    # ==========================================================
    # Get
    # ==========================================================

    async def get_record(
        self,
        record_id: uuid.UUID,
    ) -> MedicalRecord:

        record = await self.repository.get_by_uuid(
            record_id,
        )

        if (
            record is None
            or record.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Medical Record"
            )

        return record

    # ==========================================================
    # List
    # ==========================================================

    async def list_records(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> MedicalRecordListResponse:

        records = await self.repository.get_paginated(
            skip=skip,
            limit=limit,
        )

        total = await self.repository.total_count()

        return MedicalRecordListResponse(
            total=total,
            items=records,
        )

    # ==========================================================
    # Patient Records
    # ==========================================================

    async def get_patient_records(
        self,
        patient_id: uuid.UUID,
    ) -> list[MedicalRecord]:

        return await self.repository.get_by_patient(
            patient_id,
        )

    # ==========================================================
    # Update
    # ==========================================================

    async def update_record(
        self,
        *,
        record_id: uuid.UUID,
        data: MedicalRecordUpdate,
    ) -> MedicalRecord:

        record = await self.repository.get_by_uuid(
            record_id,
        )

        if (
            record is None
            or record.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Medical Record"
            )

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        async with self.uow:

            record = await self.repository.update_record(
                record,
                **update_data,
            )

        return record

    # ==========================================================
    # Delete
    # ==========================================================

    async def delete_record(
        self,
        record_id: uuid.UUID,
    ) -> None:

        record = await self.repository.get_by_uuid(
            record_id,
        )

        if (
            record is None
            or record.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Medical Record"
            )

        async with self.uow:

            await self.repository.soft_delete(
                record,
            )