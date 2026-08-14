"""
Laboratory Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


# ==========================================================
# Status
# ==========================================================

class LabStatus(str, Enum):
    ORDERED = "ORDERED"
    SAMPLE_COLLECTED = "SAMPLE_COLLECTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ==========================================================
# Create Test
# ==========================================================

class LabTestCreate(BaseModel):

    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    medical_record_id: uuid.UUID
    test_name: str


# ==========================================================
# Update Test
# ==========================================================

class LabTestUpdate(BaseModel):

    status: LabStatus | None = None
    completed_date: datetime | None = None


# ==========================================================
# Create Result
# ==========================================================

class LabResultCreate(BaseModel):

    lab_test_id: uuid.UUID
    result: str
    reference_range: str | None = None
    remarks: str | None = None
    attachment_url: str | None = None


# ==========================================================
# Result Response
# ==========================================================

class LabResultResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    lab_test_id: uuid.UUID
    result: str
    reference_range: str | None
    remarks: str | None
    attachment_url: str | None


# ==========================================================
# Test Response
# ==========================================================

class LabTestResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    test_number: str
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    medical_record_id: uuid.UUID
    test_name: str
    status: LabStatus
    requested_date: datetime
    completed_date: datetime | None


# ==========================================================
# List Response
# ==========================================================

class LabTestListResponse(BaseModel):

    total: int
    items: list[LabTestResponse]


# ==========================================================
# Message
# ==========================================================

class LaboratoryMessage(BaseModel):

    message: str