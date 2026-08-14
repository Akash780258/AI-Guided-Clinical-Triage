"""
Laboratory Service
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.core.exceptions import ResourceNotFoundException
from app.database.unit_of_work import UnitOfWork
from app.modules.auth.models import User
from app.modules.laboratory.models import (
    LabResult,
    LabStatus,
    LabTest,
)
from app.modules.laboratory.repository import LaboratoryRepository
from app.modules.laboratory.schemas import (
    LabResultCreate,
    LabResultResponse,
    LabTestCreate,
    LabTestListResponse,
    LabTestUpdate,
)


class LaboratoryService:

    def __init__(
        self,
        repository: LaboratoryRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    async def _generate_test_number(self):

        last = await self.repository.get_last_test_number()

        if last is None:
            return "LAB-000001"

        number = int(last.split("-")[1])

        return f"LAB-{number+1:06d}"

    # ==========================================================
    # Create Test
    # ==========================================================

    async def create_test(
        self,
        *,
        data: LabTestCreate,
        created_by: User,
    ):

        test = LabTest(
            test_number=await self._generate_test_number(),
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            medical_record_id=data.medical_record_id,
            test_name=data.test_name,
            status=LabStatus.ORDERED,
            requested_date=datetime.now(UTC),
            created_by_id=created_by.id,
        )

        async with self.uow:
            await self.repository.create_test(test)

        return test

    # ==========================================================
    # List
    # ==========================================================

    async def list_tests(
        self,
        skip=0,
        limit=20,
    ):

        tests = await self.repository.get_paginated(
            skip,
            limit,
        )

        total = await self.repository.total_count()

        return LabTestListResponse(
            total=total,
            items=tests,
        )

    # ==========================================================
    # Get
    # ==========================================================

    async def get_test(
        self,
        test_id: uuid.UUID,
    ):

        test = await self.repository.get_test(test_id)

        if (
            test is None
            or test.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Lab Test"
            )

        return test

    # ==========================================================
    # Update
    # ==========================================================

    async def update_test(
        self,
        *,
        test_id: uuid.UUID,
        data: LabTestUpdate,
    ):

        test = await self.get_test(test_id)

        async with self.uow:

            await self.repository.update_test(
                test,
                **data.model_dump(
                    exclude_none=True,
                    exclude_unset=True,
                ),
            )

        return test

    # ==========================================================
    # Create Result
    # ==========================================================

    async def create_result(
        self,
        data: LabResultCreate,
    ):

        test = await self.get_test(
            data.lab_test_id,
        )

        result = LabResult(
            lab_test_id=test.id,
            result=data.result,
            reference_range=data.reference_range,
            remarks=data.remarks,
            attachment_url=data.attachment_url,
        )

        async with self.uow:

            await self.repository.create_result(result)

            await self.repository.update_test(
                test,
                status=LabStatus.COMPLETED,
                completed_date=datetime.now(
                    UTC,
                ),
            )

        return LabResultResponse.model_validate(
            result,
        )

    # ==========================================================
    # Delete
    # ==========================================================

    async def delete_test(
        self,
        test_id: uuid.UUID,
    ):

        test = await self.get_test(
            test_id,
        )

        async with self.uow:

            await self.repository.soft_delete(
                test,
            )