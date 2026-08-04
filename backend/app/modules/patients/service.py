"""
Patient Service

Contains all patient business logic.
"""

from __future__ import annotations

import uuid

from app.core.exceptions import (
    ConflictException,
    ResourceNotFoundException,
)
from app.database.unit_of_work import UnitOfWork
from app.modules.auth.models import User
from app.modules.patients.models import Patient
from app.modules.patients.repository import PatientRepository
from app.modules.patients.schemas import (
    PatientCreate,
    PatientListResponse,
    PatientUpdate,
)


class PatientService:
    """
    Patient business logic.
    """

    def __init__(
        self,
        repository: PatientRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Patient Number
    # ==========================================================

    async def _generate_patient_number(self) -> str:
        """
        Generate the next patient number.

        Format:
        PAT-000001
        """

        last_patient_number = (
            await self.repository.get_last_patient_number()
        )

        if last_patient_number is None:
            return "PAT-000001"

        last_number = int(
            last_patient_number.split("-")[1]
     )

        return f"PAT-{last_number + 1:06d}"
    # ==========================================================
    # Create Patient
    # ==========================================================

    async def create_patient(
        self,
        *,
        data: PatientCreate,
        created_by: User,
    ) -> Patient:

        if await self.repository.exists_by_phone(
            data.phone,
        ):
            raise ConflictException(
                "Phone number already exists."
            )

        if (
            data.email
            and await self.repository.exists_by_email(
                data.email,
            )
        ):
            raise ConflictException(
                "Email already exists."
            )

        patient = Patient(
            patient_number=await self._generate_patient_number(),
            first_name=data.first_name,
            last_name=data.last_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            phone=data.phone,
            email=data.email,
            address=data.address,
            nationality=data.nationality,
            occupation=data.occupation,
            marital_status=data.marital_status,
            blood_group=data.blood_group,
            height=data.height,
            weight=data.weight,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_relationship=data.emergency_contact_relationship,
            emergency_contact_phone=data.emergency_contact_phone,
            insurance_provider=data.insurance_provider,
            insurance_policy_number=data.insurance_policy_number,
            profile_image_url=data.profile_image_url,
            created_by_id=created_by.id,
        )

        async with self.uow:

            await self.repository.create_patient(
                patient,
            )

        return patient

    # ==========================================================
    # Get Patient
    # ==========================================================

    
    async def get_patient(
        self,
        patient_id: uuid.UUID,
    ) -> Patient:
        """
        Get a patient by UUID.
        """

        patient = await self.repository.get_by_uuid(
            patient_id,
        )

        print("\n========== DATABASE OBJECT ==========")
        print(patient)
        print(patient.__dict__ if patient else None)
        print("=====================================\n")

        if (
            patient is None
            or patient.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Patient"
            )

        return patient
    async def list_patients(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> PatientListResponse:

        patients = await self.repository.get_paginated(
            skip=skip,
            limit=limit,
        )

        total = await self.repository.total_count()

        return PatientListResponse(
            total=total,
            items=patients,
        )
            # ==========================================================
    # Search Patients
    # ==========================================================

    async def search_patients(
        self,
        *,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> PatientListResponse:
        """
        Search patients by patient number, name,
        phone or email.
        """

        patients = await self.repository.search(
            query=query,
            skip=skip,
            limit=limit,
        )

        return PatientListResponse(
            total=len(patients),
            items=patients,
        )

    # ==========================================================
    # Update Patient
    # ==========================================================

    async def update_patient(
        self,
        *,
        patient_id: uuid.UUID,
        data: PatientUpdate,
    ) -> Patient:
        """
        Update patient information.
        """

        patient = await self.repository.get_by_uuid(
            patient_id,
        )

        if (
            patient is None
            or patient.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Patient"
            )

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        # Prevent duplicate phone
        if (
            "phone" in update_data
            and update_data["phone"] != patient.phone
        ):
            if await self.repository.exists_by_phone(
                update_data["phone"],
            ):
                raise ConflictException(
                    "Phone number already exists."
                )

        # Prevent duplicate email
        if (
            "email" in update_data
            and update_data["email"] != patient.email
            and update_data["email"] is not None
        ):
            if await self.repository.exists_by_email(
                update_data["email"],
            ):
                raise ConflictException(
                    "Email already exists."
                )

        async with self.uow:

            patient = await self.repository.update_patient(
                patient,
                **update_data,
            )

        return patient

    # ==========================================================
    # Delete Patient (Soft Delete)
    # ==========================================================

    async def delete_patient(
        self,
        patient_id: uuid.UUID,
    ) -> None:
        """
        Soft delete a patient.
        """

        patient = await self.repository.get_by_uuid(
            patient_id,
        )

        if (
            patient is None
            or patient.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Patient"
            )

        async with self.uow:

            await self.repository.soft_delete(
                patient,
            )

    # ==========================================================
    # Get By Patient Number
    # ==========================================================

    # ==========================================================
# Get By Patient Number
# ==========================================================

async def get_by_patient_number(
    self,
    patient_number: str,
) -> Patient:
    """
    Get patient using patient number.
    """

    patient = await self.repository.get_by_patient_number(
        patient_number,
    )

    if (
        patient is None
        or patient.deleted_at is not None
    ):
        raise ResourceNotFoundException(
            "Patient"
        )

    return patient