"""
Reception Service

Business logic for reception workflows.
"""

from __future__ import annotations

from datetime import date

from app.core.exceptions import ResourceNotFoundException
from app.database.unit_of_work import UnitOfWork
from app.modules.appointments.models import AppointmentStatus
from app.modules.reception.repository import ReceptionRepository
from app.modules.reception.schemas import (
    QueueItem,
    QueueResponse,
)


class ReceptionService:
    """
    Reception business logic.
    """

    def __init__(
        self,
        repository: ReceptionRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Today's Queue
    # ==========================================================

    async def get_today_queue(
        self,
        appointment_date: date,
    ) -> QueueResponse:

        appointments = await self.repository.get_today_queue(
            appointment_date,
        )

        items = [
            QueueItem(
                appointment_id=appointment.id,
                patient_id=appointment.patient.id,
                doctor_id=appointment.doctor.id,
                patient_name=f"{appointment.patient.first_name} {appointment.patient.last_name}",
                doctor_name=f"{appointment.doctor.first_name} {appointment.doctor.last_name}",
                appointment_number=appointment.appointment_number,
                status=appointment.status,
            )
            for appointment in appointments
        ]

        return QueueResponse(
            total=len(items),
            items=items,
        )

    # ==========================================================
    # Waiting Queue
    # ==========================================================

    async def get_waiting_queue(
        self,
        appointment_date: date,
    ) -> QueueResponse:

        appointments = await self.repository.get_waiting_queue(
            appointment_date,
        )

        items = [
            QueueItem(
                appointment_id=appointment.id,
                patient_id=appointment.patient.id,
                doctor_id=appointment.doctor.id,
                patient_name=f"{appointment.patient.first_name} {appointment.patient.last_name}",
                doctor_name=f"{appointment.doctor.first_name} {appointment.doctor.last_name}",
                appointment_number=appointment.appointment_number,
                status=appointment.status,
            )
            for appointment in appointments
        ]

        return QueueResponse(
            total=len(items),
            items=items,
        )

    # ==========================================================
    # Check-In
    # ==========================================================

    async def check_in(
        self,
        appointment_id,
    ):

        appointment = await self.repository.get_appointment(
            appointment_id,
        )

        if appointment is None:
            raise ResourceNotFoundException(
                "Appointment",
            )

        async with self.uow:

            appointment = await self.repository.update_status(
                appointment,
                AppointmentStatus.CHECKED_IN,
            )

        return appointment

    # ==========================================================
    # Mark Waiting
    # ==========================================================

    async def mark_waiting(
        self,
        appointment_id,
    ):

        appointment = await self.repository.get_appointment(
            appointment_id,
        )

        if appointment is None:
            raise ResourceNotFoundException(
                "Appointment",
            )

        async with self.uow:

            appointment = await self.repository.update_status(
                appointment,
                AppointmentStatus.WAITING,
            )

        return appointment

    # ==========================================================
    # Complete
    # ==========================================================

    async def complete(
        self,
        appointment_id,
    ):

        appointment = await self.repository.get_appointment(
            appointment_id,
        )

        if appointment is None:
            raise ResourceNotFoundException(
                "Appointment",
            )

        async with self.uow:

            appointment = await self.repository.update_status(
                appointment,
                AppointmentStatus.COMPLETED,
            )

        return appointment