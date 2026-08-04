"""
Doctor Service

Contains all doctor business logic.
"""

from __future__ import annotations

import uuid

from app.core.exceptions import (
    ConflictException,
    ResourceNotFoundException,
)
from app.database.unit_of_work import UnitOfWork
from app.modules.auth.models import User
from app.modules.doctors.models import Doctor
from app.modules.doctors.repository import DoctorRepository
from app.modules.doctors.schemas import (
    DoctorCreate,
    DoctorListResponse,
    DoctorUpdate,
)


class DoctorService:
    """
    Doctor business logic.
    """

    def __init__(
        self,
        repository: DoctorRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Doctor Number
    # ==========================================================

    async def _generate_doctor_number(self) -> str:
        """
        Generate the next doctor number.

        Format:
        DOC-000001
        """

        last_doctor_number = (
            await self.repository.get_last_doctor_number()
        )

        if last_doctor_number is None:
            return "DOC-000001"

        last_number = int(
            last_doctor_number.split("-")[1]
        )

        return f"DOC-{last_number + 1:06d}"

    # ==========================================================
    # Create Doctor
    # ==========================================================

    async def create_doctor(
        self,
        *,
        data: DoctorCreate,
        created_by: User,
    ) -> Doctor:

        if await self.repository.exists_by_phone(
            data.phone,
        ):
            raise ConflictException(
                "Phone number already exists."
            )

        if await self.repository.exists_by_email(
            data.email,
        ):
            raise ConflictException(
                "Email already exists."
            )

        if await self.repository.exists_by_license(
            data.license_number,
        ):
            raise ConflictException(
                "License number already exists."
            )

        doctor = Doctor(
            doctor_number=await self._generate_doctor_number(),
            first_name=data.first_name,
            last_name=data.last_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            phone=data.phone,
            email=data.email,
            department=data.department,
            specialization=data.specialization,
            qualification=data.qualification,
            experience_years=data.experience_years,
            license_number=data.license_number,
            consultation_fee=data.consultation_fee,
            profile_image_url=data.profile_image_url,
            is_available=data.is_available,
            created_by_id=created_by.id,
        )

        async with self.uow:

            await self.repository.create_doctor(
                doctor,
            )

        return doctor

    # ==========================================================
    # Get Doctor
    # ==========================================================

    async def get_doctor(
        self,
        doctor_id: uuid.UUID,
    ) -> Doctor:

        doctor = await self.repository.get_by_uuid(
            doctor_id,
        )

        if (
            doctor is None
            or doctor.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Doctor"
            )

        return doctor

    # ==========================================================
    # List Doctors
    # ==========================================================

    async def list_doctors(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> DoctorListResponse:

        doctors = await self.repository.get_paginated(
            skip=skip,
            limit=limit,
        )

        total = await self.repository.total_count()

        return DoctorListResponse(
            total=total,
            items=doctors,
        )

    # ==========================================================
    # Search Doctors
    # ==========================================================

    async def search_doctors(
        self,
        *,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> DoctorListResponse:

        doctors = await self.repository.search(
            query=query,
            skip=skip,
            limit=limit,
        )

        return DoctorListResponse(
            total=len(doctors),
            items=doctors,
        )

    # ==========================================================
    # Update Doctor
    # ==========================================================

    async def update_doctor(
        self,
        *,
        doctor_id: uuid.UUID,
        data: DoctorUpdate,
    ) -> Doctor:

        doctor = await self.repository.get_by_uuid(
            doctor_id,
        )

        if (
            doctor is None
            or doctor.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Doctor"
            )

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if (
            "phone" in update_data
            and update_data["phone"] != doctor.phone
        ):
            if await self.repository.exists_by_phone(
                update_data["phone"],
            ):
                raise ConflictException(
                    "Phone number already exists."
                )

        if (
            "email" in update_data
            and update_data["email"] != doctor.email
        ):
            if await self.repository.exists_by_email(
                update_data["email"],
            ):
                raise ConflictException(
                    "Email already exists."
                )

        if (
            "license_number" in update_data
            and update_data["license_number"] != doctor.license_number
        ):
            if await self.repository.exists_by_license(
                update_data["license_number"],
            ):
                raise ConflictException(
                    "License number already exists."
                )

        async with self.uow:

            doctor = await self.repository.update_doctor(
                doctor,
                **update_data,
            )

        return doctor

    # ==========================================================
    # Delete Doctor
    # ==========================================================

    async def delete_doctor(
        self,
        doctor_id: uuid.UUID,
    ) -> None:

        doctor = await self.repository.get_by_uuid(
            doctor_id,
        )

        if (
            doctor is None
            or doctor.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Doctor"
            )

        async with self.uow:

            await self.repository.soft_delete(
                doctor,
            )

    # ==========================================================
    # Get By Doctor Number
    # ==========================================================

    async def get_by_doctor_number(
        self,
        doctor_number: str,
    ) -> Doctor:

        doctor = await self.repository.get_by_doctor_number(
            doctor_number,
        )

        if doctor is None:
            raise ResourceNotFoundException(
                "Doctor"
            )

        return doctor