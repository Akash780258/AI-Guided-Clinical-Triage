"""
Appointment Service

Contains all appointment business logic.
"""

from __future__ import annotations

import uuid

from app.core.exceptions import (
    ConflictException,
    ResourceNotFoundException,
)
from app.database.unit_of_work import UnitOfWork
from app.modules.auth.models import User
from app.modules.appointments.models import (
    Appointment,
    AppointmentStatus,
)
from app.modules.appointments.repository import (
    AppointmentRepository,
)
from app.modules.appointments.schemas import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentUpdate,
)


class AppointmentService:
    """
    Appointment business logic.
    """

    def __init__(
        self,
        repository: AppointmentRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Appointment Number
    # ==========================================================

    async def _generate_appointment_number(
        self,
    ) -> str:
        """
        Generate the next appointment number.

        Format:
        APT-000001
        """

        last_appointment_number = (
            await self.repository.get_last_appointment_number()
        )

        if last_appointment_number is None:
            return "APT-000001"

        last_number = int(
            last_appointment_number.split("-")[1]
        )

        return f"APT-{last_number + 1:06d}"

    # ==========================================================
    # Create Appointment
    # ==========================================================

    async def create_appointment(
        self,
        *,
        data: AppointmentCreate,
        created_by: User,
    ) -> Appointment:

        appointment = Appointment(
            appointment_number=await self._generate_appointment_number(),
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            appointment_date=data.appointment_date,
            start_time=data.start_time,
            end_time=data.end_time,
            reason=data.reason,
            notes=data.notes,
            status=AppointmentStatus.SCHEDULED,
            created_by_id=created_by.id,
        )

        async with self.uow:

            await self.repository.create_appointment(
                appointment,
            )

        return appointment

    # ==========================================================
    # Get Appointment
    # ==========================================================

    async def get_appointment(
        self,
        appointment_id: uuid.UUID,
    ) -> Appointment:

        appointment = await self.repository.get_by_uuid(
            appointment_id,
        )

        if (
            appointment is None
            or appointment.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Appointment"
            )

        return appointment
            # ==========================================================
    # List Appointments
    # ==========================================================

    async def list_appointments(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> AppointmentListResponse:

        appointments = await self.repository.get_paginated(
            skip=skip,
            limit=limit,
        )

        total = await self.repository.total_count()

        return AppointmentListResponse(
            total=total,
            items=appointments,
        )

    # ==========================================================
    # Today's Appointments
    # ==========================================================

    async def list_today(
        self,
        appointment_date,
    ) -> AppointmentListResponse:
        """
        Returns today's appointments.
        """

        appointments = await self.repository.get_today(
            appointment_date,
        )

        return AppointmentListResponse(
            total=len(appointments),
            items=appointments,
        )

    # ==========================================================
    # Doctor Appointments
    # ==========================================================

    async def list_by_doctor(
        self,
        doctor_id: uuid.UUID,
    ) -> AppointmentListResponse:
        """
        Returns appointments for a doctor.
        """

        appointments = await self.repository.get_by_doctor(
            doctor_id,
        )

        return AppointmentListResponse(
            total=len(appointments),
            items=appointments,
        )

    # ==========================================================
    # Patient Appointments
    # ==========================================================

    async def list_by_patient(
        self,
        patient_id: uuid.UUID,
    ) -> AppointmentListResponse:
        """
        Returns appointments for a patient.
        """

        appointments = await self.repository.get_by_patient(
            patient_id,
        )

        return AppointmentListResponse(
            total=len(appointments),
            items=appointments,
        )

    # ==========================================================
    # Get By Appointment Number
    # ==========================================================

    async def get_by_appointment_number(
        self,
        appointment_number: str,
    ) -> Appointment:

        appointment = (
            await self.repository.get_by_appointment_number(
                appointment_number,
            )
        )

        if (
            appointment is None
            or appointment.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Appointment"
            )

        return appointment
            # ==========================================================
    # Update Appointment
    # ==========================================================

    async def update_appointment(
        self,
        *,
        appointment_id: uuid.UUID,
        data: AppointmentUpdate,
    ) -> Appointment:

        appointment = await self.repository.get_by_uuid(
            appointment_id,
        )

        if (
            appointment is None
            or appointment.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Appointment"
            )

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        async with self.uow:

            appointment = await self.repository.update_appointment(
                appointment,
                **update_data,
            )

        return appointment

    # ==========================================================
    # Cancel Appointment
    # ==========================================================

    async def cancel_appointment(
        self,
        appointment_id: uuid.UUID,
    ) -> Appointment:

        appointment = await self.repository.get_by_uuid(
            appointment_id,
        )

        if (
            appointment is None
            or appointment.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Appointment"
            )

        async with self.uow:

            appointment = await self.repository.update_appointment(
                appointment,
                status=AppointmentStatus.CANCELLED,
            )

        return appointment

    # ==========================================================
    # Delete Appointment (Soft Delete)
    # ==========================================================

    async def delete_appointment(
        self,
        appointment_id: uuid.UUID,
    ) -> None:

        appointment = await self.repository.get_by_uuid(
            appointment_id,
        )

        if (
            appointment is None
            or appointment.deleted_at is not None
        ):
            raise ResourceNotFoundException(
                "Appointment"
            )

        async with self.uow:

            await self.repository.soft_delete(
                appointment,
            )
            