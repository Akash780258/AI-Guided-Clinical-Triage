"""
AGCT — Digital Twin / Clinical Intelligence Module
===================================================

Purpose
-------
Read-only, patient-scoped clinical intelligence for the AGCT doctor UI.

This module provides:
- Patient-specific Digital Twin analysis
- Patient-specific AI chat using local Ollama
- Deterministic laboratory extraction/comparison
- Clinical suggestions / evidence summary
- Patient overview for the dashboard
- Clinical timeline
- Findings and review alerts
- Frontend-friendly body/anatomical map data
- One aggregated dashboard endpoint
- Human-friendly PAT-xxxxx identifiers in responses
- Internal UUID isolation for all database access
- Explicit separation of clinical vs ignored documents
- Synthetic/test-document transparency
- Defensive handling of missing/unknown data
- Ollama connectivity/error handling

Safety boundary
---------------
The module is an evidence/retrieval/summarization layer.

It does NOT:
- diagnose a patient
- prescribe medication
- change medication
- modify patient records
- invent undocumented values
- use unrelated/ignored documents as clinical evidence

Synthetic/test clinical documents remain usable evidence for software
testing, but are explicitly labelled as synthetic/test data.

The frontend should select a patient by patient_number/name and keep the
internal UUID in application state. Doctors should not manually type UUIDs.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import date, datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import DoctorOnly
from app.database.session import get_db

from app.modules.auth.models import User
from app.modules.patients.models import Patient
from app.modules.patients.documents import PatientDocument
from app.modules.medical_records.models import MedicalRecord
from app.modules.laboratory.models import LabTest, LabResult
from app.modules.prescriptions.models import Prescription


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/digital-twin",
    tags=["Digital Twin"],
)


# ==========================================================
# Constants
# ==========================================================

CLINICAL_DOCUMENT_TYPES = {
    "LAB_REPORT",
    "PRESCRIPTION",
    "MEDICAL_REPORT",
    "IMAGING_REPORT",
    "DISCHARGE_SUMMARY",
}

COMPLETED_STATUS = "COMPLETED"

MODEL_FALLBACK = "llama3.2:3b"
OLLAMA_URL_FALLBACK = "http://127.0.0.1:11434"
OLLAMA_TIMEOUT_FALLBACK = 180.0

MAX_DOCUMENT_CHARS_FOR_OLLAMA = 12000
MAX_TOTAL_CONTEXT_CHARS_FOR_OLLAMA = 50000

DISCLAIMER = (
    "Evidence summary only. This endpoint does not provide a "
    "diagnosis or treatment recommendation."
)

NO_DOCUMENTED_VALUE = (
    "I could not find a documented value for that in this patient's records."
)


# ==========================================================
# Request Models
# ==========================================================

class DigitalTwinChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description="Question about the currently selected patient.",
    )


class DigitalTwinAnalyzeRequest(BaseModel):
    """Controls whether the slow Ollama narrative is requested."""

    run_ai: bool = Field(
        default=False,
        description=(
            "When true, also run the local Ollama narrative analysis. "
            "The default is false so document uploads and dashboard refreshes "
            "are never blocked by a slow LLM request."
        ),
    )


# ==========================================================
# Generic Helpers
# ==========================================================

def serialize_value(value: Any) -> Any:
    """Convert common database values into JSON-safe values."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, uuid.UUID):
        return str(value)

    return value


def enum_token(value: Any, default: str = "") -> str:
    """
    Normalize SQLAlchemy Enum values and strings.

    Supports:
      DocumentType.LAB_REPORT
      LAB_REPORT
      <Enum value>
    """
    if value is None:
        return default

    raw = getattr(value, "value", value)
    text = str(raw).strip().upper()

    if "." in text:
        text = text.rsplit(".", 1)[-1]

    return text or default


def clean_text(value: Any) -> str:
    """Normalize arbitrary text without inventing content."""
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def parse_float(value: Any) -> float | None:
    """Parse a numeric value safely."""
    if value is None:
        return None

    text = clean_text(value)

    if not text:
        return None

    # Keep decimal notation and sign only.
    text = re.sub(
        r"[^0-9.+\-]",
        "",
        text,
    )

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def parse_date_for_sort(value: Any) -> datetime:
    """
    Convert common date/datetime strings to a sortable datetime.
    Unknown dates sort last.
    """
    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(
            value,
            datetime.min.time(),
        )

    if value is None:
        return datetime.max

    text = clean_text(value)

    if not text:
        return datetime.max

    # ISO first.
    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        ).replace(tzinfo=None)
    except ValueError:
        pass

    for fmt in (
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
    ):
        try:
            return datetime.strptime(
                text,
                fmt,
            )
        except ValueError:
            continue

    return datetime.max


def model_name() -> str:
    return (
        getattr(
            settings,
            "DEFAULT_CHAT_MODEL",
            None,
        )
        or MODEL_FALLBACK
    )


def ollama_base_url() -> str:
    return (
        getattr(
            settings,
            "OLLAMA_BASE_URL",
            None,
        )
        or OLLAMA_URL_FALLBACK
    ).rstrip("/")


def ollama_timeout() -> float:
    value = getattr(
        settings,
        "OLLAMA_TIMEOUT_SECONDS",
        OLLAMA_TIMEOUT_FALLBACK,
    )

    try:
        return max(
            10.0,
            float(value),
        )
    except (TypeError, ValueError):
        return OLLAMA_TIMEOUT_FALLBACK


def is_deleted_clause(model: Any):
    """
    Build a deleted_at condition when the model exposes soft delete.
    Current AGCT models use deleted_at; the fallback makes this module
    safer if a future model omits the column.
    """
    column = getattr(
        model,
        "deleted_at",
        None,
    )

    if column is None:
        return None

    return column.is_(None)


def apply_patient_scope(
    statement: Any,
    model: Any,
    patient_id: uuid.UUID,
):
    """Apply patient and soft-delete scope defensively."""
    statement = statement.where(
        model.patient_id == patient_id
    )

    deleted_clause = is_deleted_clause(model)

    if deleted_clause is not None:
        statement = statement.where(
            deleted_clause
        )

    return statement


# ==========================================================
# Patient Serialization
# ==========================================================

def patient_to_dict(
    patient: Patient,
) -> dict:
    """Serialize only safe patient profile information."""
    return {
        "id": serialize_value(
            patient.id
        ),
        "patient_number": getattr(
            patient,
            "patient_number",
            None,
        ),
        "first_name": getattr(
            patient,
            "first_name",
            None,
        ),
        "last_name": getattr(
            patient,
            "last_name",
            None,
        ),
        "date_of_birth": serialize_value(
            getattr(
                patient,
                "date_of_birth",
                None,
            )
        ),
        "gender": (
            enum_token(
                getattr(
                    patient,
                    "gender",
                    None,
                ),
                default="",
            )
            or None
        ),
        "phone": getattr(
            patient,
            "phone",
            None,
        ),
        "email": getattr(
            patient,
            "email",
            None,
        ),
        "address": getattr(
            patient,
            "address",
            None,
        ),
        "nationality": getattr(
            patient,
            "nationality",
            None,
        ),
        "occupation": getattr(
            patient,
            "occupation",
            None,
        ),
        "marital_status": (
            enum_token(
                getattr(
                    patient,
                    "marital_status",
                    None,
                ),
                default="",
            )
            or None
        ),
        "blood_group": (
            enum_token(
                getattr(
                    patient,
                    "blood_group",
                    None,
                ),
                default="",
            )
            or None
        ),
        "height": getattr(
            patient,
            "height",
            None,
        ),
        "weight": getattr(
            patient,
            "weight",
            None,
        ),
    }


# ==========================================================
# Clinical Document Helpers
# ==========================================================

def document_is_clinical(
    document: PatientDocument,
) -> bool:
    """True only for completed, classified clinical documents."""
    doc_type = enum_token(
        getattr(
            document,
            "document_type",
            None,
        ),
        default="UNCLASSIFIED",
    )

    processing_status = enum_token(
        getattr(
            document,
            "processing_status",
            None,
        ),
        default="UNKNOWN",
    )

    extracted_text = clean_text(
        getattr(
            document,
            "extracted_text",
            None,
        )
    )

    return (
        doc_type in CLINICAL_DOCUMENT_TYPES
        and processing_status == COMPLETED_STATUS
        and bool(extracted_text)
    )


def document_is_synthetic(
    extracted_text: str,
) -> bool:
    """Detect explicit test/synthetic wording only."""
    lowered = (
        extracted_text or ""
    ).lower()

    markers = (
        "synthetic",
        "fictional",
        "sample",
        "software testing",
        "test data",
        "not a real medical report",
        "for testing only",
    )

    return any(
        marker in lowered
        for marker in markers
    )


def document_to_dict(
    document: PatientDocument,
    include_text: bool = True,
) -> dict:
    """Serialize an uploaded patient document."""
    text = clean_text(
        getattr(
            document,
            "extracted_text",
            None,
        )
    )

    result = {
        "document_id": str(
            document.id
        ),
        "filename": (
            getattr(
                document,
                "original_filename",
                None,
            )
            or getattr(
                document,
                "filename",
                None,
            )
        ),
        "content_type": getattr(
            document,
            "content_type",
            None,
        ),
        "document_type": enum_token(
            getattr(
                document,
                "document_type",
                None,
            ),
            default="UNCLASSIFIED",
        ),
        "processing_status": enum_token(
            getattr(
                document,
                "processing_status",
                None,
            ),
            default="UNKNOWN",
        ),
        "created_at": serialize_value(
            getattr(
                document,
                "created_at",
                None,
            )
        ),
        "synthetic": document_is_synthetic(
            text
        ),
    }

    if include_text:
        result["extracted_text"] = text

    return result


# ==========================================================
# Lab Helpers
# ==========================================================

LAB_TEST_ALIASES = {
    "blood glucose": (
        "blood glucose",
        "glucose",
        "blood sugar",
        "fasting blood glucose",
        "fasting glucose",
        "random blood glucose",
        "random glucose",
        "fbs",
        "rbs",
    ),

    "hba1c": (
        "hba1c",
        "hb a1c",
        "hb-a1c",
        "glycated hemoglobin",
        "glycosylated hemoglobin",
    ),

    "hemoglobin": (
        "hemoglobin",
        "haemoglobin",
        "hemoglobin level",
        "haemoglobin level",
    ),

    "total cholesterol": (
        "total cholesterol",
        "total chol",
    ),

    "ldl cholesterol": (
        "ldl cholesterol",
        "ldl-cholesterol",
        "ldl chol",
        "ldl",
        "low density lipoprotein",
        "low-density lipoprotein",
    ),

    "hdl cholesterol": (
        "hdl cholesterol",
        "hdl-cholesterol",
        "hdl chol",
        "hdl",
        "high density lipoprotein",
        "high-density lipoprotein",
    ),

    "triglycerides": (
        "triglycerides",
        "triglyceride",
        "triglyceride level",
        "tg",
    ),

    "resting heart rate": (
        "resting heart rate",
        "heart rate",
    ),

    "qtc interval": (
        "qtc interval",
        "qtc",
    ),

    "troponin i": (
        "troponin i",
        "troponin",
    ),

    "ejection fraction": (
        "ejection fraction",
    ),

    "oxygen saturation": (
        "oxygen saturation",
        "spo2",
        "spO2",
    ),

    "respiratory rate": (
        "respiratory rate",
        "resp rate",
    ),

    "fev1": (
        "fev1",
        "fev 1",
    ),

    "blood pressure": (
        "blood pressure",
        "bp",
    ),

    "crp": (
        "crp",
        "c-reactive protein",
        "c reactive protein",
    ),
}


LAB_ALIAS_TO_CANONICAL = {
    alias.lower(): canonical
    for canonical, aliases in LAB_TEST_ALIASES.items()
    for alias in aliases
}


def normalize_reference(reference: Any) -> str:
    """Normalize OCR reference ranges without changing meaning."""
    return clean_text(
        reference
    ).replace(
        "−",
        "-",
    )


def parse_reference_range(
    reference: str,
) -> dict:
    """
    Parse only explicitly documented reference formats:
      70-100
      70–100
      <5.7
      <=5.7
      >10
      >=10
    """
    ref = normalize_reference(
        reference
    )

    if not ref:
        return {
            "kind": "unknown",
            "low": None,
            "high": None,
            "raw": "",
            "inclusive": False,
        }

    upper = re.fullmatch(
        r"(<=|<)\s*(\d+(?:\.\d+)?)",
        ref,
    )

    if upper:
        return {
            "kind": "upper",
            "low": None,
            "high": float(
                upper.group(2)
            ),
            "raw": ref,
            "inclusive": (
                upper.group(1) == "<="
            ),
        }

    lower = re.fullmatch(
        r"(>=|>)\s*(\d+(?:\.\d+)?)",
        ref,
    )

    if lower:
        return {
            "kind": "lower",
            "low": float(
                lower.group(2)
            ),
            "high": None,
            "raw": ref,
            "inclusive": (
                lower.group(1) == ">="
            ),
        }

    interval = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)",
        ref,
    )

    if interval:
        return {
            "kind": "range",
            "low": float(
                interval.group(1)
            ),
            "high": float(
                interval.group(2)
            ),
            "raw": ref,
            "inclusive": True,
        }

    return {
        "kind": "unknown",
        "low": None,
        "high": None,
        "raw": ref,
        "inclusive": False,
    }


def compare_to_reference(
    value: Any,
    reference: Any,
) -> str:
    """
    Compare a documented result only against its documented range.
    Never invents a medical reference range.
    """
    numeric_value = parse_float(
        value
    )

    if numeric_value is None:
        return "UNKNOWN"

    parsed = parse_reference_range(
        clean_text(reference)
    )

    kind = parsed["kind"]

    if kind == "range":
        low = parsed["low"]
        high = parsed["high"]

        if low <= numeric_value <= high:
            return "WITHIN_STATED_RANGE"

        if numeric_value < low:
            return "BELOW_STATED_RANGE"

        return "ABOVE_STATED_RANGE"

    if kind == "upper":
        high = parsed["high"]

        if parsed["inclusive"]:
            return (
                "WITHIN_STATED_RANGE"
                if numeric_value <= high
                else "ABOVE_STATED_RANGE"
            )

        return (
            "WITHIN_STATED_RANGE"
            if numeric_value < high
            else "ABOVE_STATED_RANGE"
        )

    if kind == "lower":
        low = parsed["low"]

        if parsed["inclusive"]:
            return (
                "WITHIN_STATED_RANGE"
                if numeric_value >= low
                else "BELOW_STATED_RANGE"
            )

        return (
            "WITHIN_STATED_RANGE"
            if numeric_value > low
            else "BELOW_STATED_RANGE"
        )

    return "UNKNOWN"


def extract_report_date(
    extracted_text: str,
) -> str | None:
    """Extract a clearly labelled report/date field from OCR text."""
    text = clean_text(
        extracted_text
    )

    if not text:
        return None

    patterns = (
        r"\breport\s+date\b\s*(?::|-|=)?\s*("
        r"\d{1,2}\s+[A-Za-z]+\s+\d{4}|"
        r"[A-Za-z]+\s+\d{1,2},\s*\d{4}|"
        r"\d{4}-\d{2}-\d{2}|"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{4}"
        r")",
        r"\bdate\b\s*(?::|-|=)\s*("
        r"\d{1,2}\s+[A-Za-z]+\s+\d{4}|"
        r"[A-Za-z]+\s+\d{1,2},\s*\d{4}|"
        r"\d{4}-\d{2}-\d{2}|"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{4}"
        r")",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return clean_text(
                match.group(1)
            )

    return None


def extract_lab_rows_from_document(
    extracted_text: str,
) -> list[dict]:
    """
    Extract explicitly documented numeric clinical measurements.

    The parser supports the normal table layouts used by AGCT synthetic
    reports, including:
        Test 112 bpm 60-100 bpm
        Test 0.08 ng/mL <0.04 ng/mL
        Test 48% 55-70%
        Test 68% predicted >80% predicted

    This function only extracts values/ranges present in the source text.
    It does not invent clinical reference ranges.
    """
    text = clean_text(extracted_text)

    if not text:
        return []

    # Repair common PDF/OCR mojibake seen in the existing reports.
    replacements = {
        "â€“": "-",
        "â€”": "-",
        "âˆ’": "-",
        "â‰¤": "<=",
        "â‰¥": ">=",
        "â‰¤": "<=",
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
        "â€¢": " ",
        "■": "2",
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    report_date = extract_report_date(text)

    aliases = sorted(
        LAB_ALIAS_TO_CANONICAL.keys(),
        key=len,
        reverse=True,
    )

    alias_pattern = "|".join(
        re.escape(alias)
        for alias in aliases
    )

    # Match a test name followed by a value. The text between value and
    # reference may contain a unit, "predicted", or other source wording.
    pattern = re.compile(
        rf"""
        (?P<test>{alias_pattern})
        \s*
        (?::|-|=)?
        \s*
        (?P<value>[+-]?\d+(?:\.\d+)?)
        \s*
        (?P<middle>
            (?:%|/[A-Za-z]+|[A-Za-zµμ]+(?:\s*/\s*[A-Za-z]+)?)
            (?:\s+predicted)?
        )?
        \s*
        (?P<reference>
            <=?\s*[+-]?\d+(?:\.\d+)?
            |
            >=?\s*[+-]?\d+(?:\.\d+)?
            |
            \d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?
        )?
        """,
        flags=re.IGNORECASE | re.VERBOSE,
    )

    rows: list[dict] = []

    for match in pattern.finditer(text):
        raw_test = clean_text(
            match.group("test")
        ).lower()

        canonical = LAB_ALIAS_TO_CANONICAL.get(
            raw_test,
            raw_test,
        )

        value = clean_text(
            match.group("value")
        )

        middle = clean_text(
            match.group("middle")
        )

        reference = normalize_reference(
            match.group("reference")
        )

        # Some PDFs put the unit/reference in a slightly different order.
        window = text[
            match.end("value"):
            min(len(text), match.end("value") + 80)
        ]

        if not reference:
            ref_match = re.search(
                r"""
                (
                    <=?\s*[+-]?\d+(?:\.\d+)?
                    |
                    >=?\s*[+-]?\d+(?:\.\d+)?
                    |
                    \d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?
                )
                """,
                window,
                flags=re.IGNORECASE | re.VERBOSE,
            )

            if ref_match:
                reference = normalize_reference(
                    ref_match.group(1)
                )

        unit = ""

        unit_match = re.search(
            r"""
            (?:
                %
                |
                mg\s*/?\s*dL
                |
                mmol\s*/?\s*L
                |
                g\s*/?\s*dL
                |
                mEq\s*/?\s*L
                |
                IU\s*/?\s*L
                |
                U\s*/?\s*L
                |
                ng\s*/?\s*mL
                |
                ms
                |
                bpm
                |
                mmHg
                |
                breaths?\s*/?\s*min
                |
                /min
            )
            """,
            middle + " " + window,
            flags=re.IGNORECASE | re.VERBOSE,
        )

        if unit_match:
            unit = clean_text(
                unit_match.group(0)
            )

        rows.append(
            {
                "test_name": canonical,
                "value": value,
                "unit": unit,
                "reference_range": reference,
                "date": report_date,
                "status": compare_to_reference(
                    value,
                    reference,
                ),
            }
        )

    unique: list[dict] = []
    seen: set[tuple] = set()

    for row in rows:
        key = (
            row["test_name"],
            row["value"],
            row["unit"],
            row["reference_range"],
            row["date"],
        )

        if key not in seen:
            seen.add(key)
            unique.append(row)

    return unique


def structured_lab_to_dict(
    lab_test: LabTest,
    lab_result: LabResult | None,
) -> dict:
    """
    Convert a structured lab result while tolerating optional
    unit/date fields across model versions.
    """
    result = (
        getattr(
            lab_result,
            "result",
            None,
        )
        if lab_result is not None
        else None
    )

    reference = (
        getattr(
            lab_result,
            "reference_range",
            None,
        )
        if lab_result is not None
        else None
    )

    # Unit field names differ across implementations.
    unit = ""
    if lab_result is not None:
        for key in (
            "unit",
            "units",
            "result_unit",
        ):
            candidate = getattr(
                lab_result,
                key,
                None,
            )

            if candidate:
                unit = clean_text(
                    candidate
                )
                break

    completed = getattr(
        lab_test,
        "completed_date",
        None,
    )

    requested = getattr(
        lab_test,
        "requested_date",
        None,
    )

    test_name = clean_text(
        getattr(
            lab_test,
            "test_name",
            "",
        )
    )

    return {
        "source": "structured_lab_result",
        "test_name": test_name,
        "value": (
            clean_text(result)
            if result is not None
            else ""
        ),
        "unit": unit,
        "reference_range": normalize_reference(
            reference
        ),
        "status": compare_to_reference(
            result,
            reference,
        ),
        "date": serialize_value(
            completed or requested
        ),
        "synthetic": False,
        "document_id": None,
        "filename": None,
    }


def extract_verified_laboratory_findings(
    clinical_context: dict,
) -> list[dict]:
    """
    Produce one deduplicated evidence list from structured lab results
    and classified clinical documents.
    """
    findings: list[dict] = []

    # Structured results first.
    for lab in clinical_context.get(
        "laboratory",
        [],
    ):
        if lab.get("result") in (
            None,
            "",
        ):
            continue

        findings.append(
            {
                "source": "structured_lab_result",
                "test_name": clean_text(
                    lab.get(
                        "test_name",
                        "",
                    )
                ),
                "value": clean_text(
                    lab.get(
                        "result",
                        "",
                    )
                ),
                "unit": clean_text(
                    lab.get(
                        "unit",
                        "",
                    )
                ),
                "reference_range": normalize_reference(
                    lab.get(
                        "reference_range",
                        "",
                    )
                ),
                "status": compare_to_reference(
                    lab.get(
                        "result",
                        "",
                    ),
                    lab.get(
                        "reference_range",
                        "",
                    ),
                ),
                "date": (
                    lab.get("completed_date")
                    or lab.get("requested_date")
                ),
                "synthetic": False,
                "document_id": None,
                "filename": None,
            }
        )

    # Classified documents.
    for document in clinical_context.get(
        "clinical_documents",
        [],
    ):
        text = clean_text(
            document.get(
                "extracted_text",
                "",
            )
        )

        if not text:
            continue

        rows = extract_lab_rows_from_document(
            text
        )

        synthetic = document_is_synthetic(
            text
        )

        for row in rows:
            findings.append(
                {
                    **row,
                    "source": "clinical_document",
                    "document_id": document.get(
                        "document_id"
                    ),
                    "filename": document.get(
                        "filename"
                    ),
                    "synthetic": synthetic,
                }
            )

    # Deduplicate while preserving structured data first.
    unique: list[dict] = []
    seen: set[tuple] = set()

    for finding in findings:
        key = (
            clean_text(
                finding.get(
                    "test_name"
                )
            ).lower(),
            clean_text(
                finding.get(
                    "value"
                )
            ),
            clean_text(
                finding.get(
                    "unit"
                )
            ).lower(),
            clean_text(
                finding.get(
                    "reference_range"
                )
            ),
            serialize_value(
                finding.get(
                    "date"
                )
            ),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(finding)

    return unique


# ==========================================================
# Clinical Evidence / Suggestions
# ==========================================================

def build_clinical_intelligence(
    clinical_context: dict,
) -> dict:
    """Build deterministic laboratory intelligence."""
    findings = extract_verified_laboratory_findings(
        clinical_context
    )

    abnormal = [
        item
        for item in findings
        if item.get("status")
        in {
            "ABOVE_STATED_RANGE",
            "BELOW_STATED_RANGE",
        }
    ]

    unknown = [
        item
        for item in findings
        if item.get("status") == "UNKNOWN"
    ]

    follow_up = []

    for item in abnormal:
        direction = (
            "above"
            if item["status"]
            == "ABOVE_STATED_RANGE"
            else "below"
        )

        unit = (
            f" {item['unit']}"
            if item.get("unit")
            else ""
        )

        reference = (
            item.get(
                "reference_range"
            )
            or "the documented reference range"
        )

        text = (
            f"{item['test_name']}: "
            f"{item['value']}{unit} is {direction} "
            f"the stated reference range ({reference}). "
            "A qualified healthcare professional should "
            "review this result in the appropriate clinical context."
        )

        if item.get("synthetic"):
            text += (
                " The source document is explicitly marked "
                "as synthetic/test data."
            )

        follow_up.append(text)

    return {
        "all_findings": findings,
        "abnormal_findings": abnormal,
        "unknown_reference_findings": unknown,
        "suggested_follow_up": follow_up,
    }


def question_requests_clinical_suggestions(
    question: str,
) -> bool:
    q = clean_text(
        question
    ).lower()

    phrases = (
        "abnormal",
        "abnormality",
        "abnormalities",
        "out of range",
        "outside range",
        "outside their range",
        "outside the range",
        "follow-up",
        "follow up",
        "what should the doctor",
        "what should doctor",
        "clinical concern",
        "clinical concerns",
        "clinical suggestion",
        "clinical suggestions",
        "requiring review",
        "requires review",
    )

    return any(
        phrase in q
        for phrase in phrases
    )


def format_clinical_suggestions(
    clinical_context: dict,
) -> str | None:
    intelligence = build_clinical_intelligence(
        clinical_context
    )

    findings = intelligence[
        "all_findings"
    ]

    if not findings:
        return None

    abnormal = intelligence[
        "abnormal_findings"
    ]

    if not abnormal:
        return (
            "No laboratory result in the available "
            "clinical evidence was found to be outside "
            "its explicitly documented reference range. "
            "This does not establish that all clinical "
            "findings are normal."
        )

    lines = [
        "Documented laboratory findings requiring clinical review:"
    ]

    for item in abnormal:
        direction = (
            "above"
            if item["status"]
            == "ABOVE_STATED_RANGE"
            else "below"
        )

        unit = (
            f" {item['unit']}"
            if item.get("unit")
            else ""
        )

        reference = (
            item.get(
                "reference_range"
            )
            or "not specified"
        )

        date_text = (
            f" on {item['date']}"
            if item.get("date")
            else ""
        )

        line = (
            f"- {item['test_name']}: "
            f"{item['value']}{unit}; {direction} "
            f"the stated reference range ({reference})"
            f"{date_text}."
        )

        if item.get("synthetic"):
            line += (
                " Source is explicitly marked "
                "synthetic/test data."
            )

        lines.append(line)

    lines.append(
        "Suggested follow-up: a qualified healthcare "
        "professional should review these documented "
        "findings in the full clinical context."
    )

    lines.append(
        "This is an evidence summary, not a diagnosis "
        "or treatment recommendation."
    )

    return "\n".join(
        lines
    )


# ==========================================================
# Deterministic Question Retrieval
# ==========================================================

GLUCOSE_TERMS = (
    "blood sugar",
    "blood glucose",
    "glucose",
    "fasting glucose",
    "fasting blood glucose",
    "random blood glucose",
    "fbs",
    "rbs",
)

MEDICATION_TERMS = (
    "medication",
    "medications",
    "medicine",
    "medicines",
    "prescription",
    "prescriptions",
    "drugs",
)

DIAGNOSIS_TERMS = (
    "diagnosis",
    "diagnoses",
    "diagnosed",
    "condition",
    "conditions",
)

def question_year(
    question: str,
) -> str | None:
    match = re.search(
        r"\b(19|20)\d{2}\b",
        question,
    )

    return (
        match.group(0)
        if match
        else None
    )


def document_contains_year(
    document: dict,
    year: str | None,
) -> bool:
    if not year:
        return True

    text = clean_text(
        document.get(
            "extracted_text",
            "",
        )
    )

    return year in text


def deterministic_glucose_answer(
    clinical_context: dict,
    question: str,
) -> str | None:
    """Retrieve an exact documented glucose result if available."""
    q = clean_text(
        question
    ).lower()

    if not any(
        term in q
        for term in GLUCOSE_TERMS
    ):
        return None

    year = question_year(
        question
    )

    # Structured database first.
    for lab in clinical_context.get(
        "laboratory",
        [],
    ):
        name = clean_text(
            lab.get(
                "test_name",
                "",
            )
        ).lower()

        if not any(
            term in name
            for term in GLUCOSE_TERMS
        ):
            continue

        value = lab.get(
            "result"
        )

        if value in (
            None,
            "",
        ):
            continue

        date_value = (
            lab.get(
                "completed_date"
            )
            or lab.get(
                "requested_date"
            )
        )

        date_text = clean_text(
            date_value
        )

        if (
            year
            and year not in date_text
        ):
            continue

        unit = clean_text(
            lab.get(
                "unit",
                "",
            )
        )

        reference = clean_text(
            lab.get(
                "reference_range",
                "",
            )
        )

        answer = (
            f"The patient's documented "
            f"{lab.get('test_name', 'blood glucose')} "
            f"was {clean_text(value)}"
        )

        if unit:
            answer += f" {unit}"

        if date_text:
            answer += f" on {date_text}"

        if reference:
            answer += (
                f" (documented reference range: "
                f"{reference})"
            )

        return answer + "."

    # Clinical documents.
    for document in clinical_context.get(
        "clinical_documents",
        [],
    ):
        if not document_contains_year(
            document,
            year,
        ):
            continue

        text = clean_text(
            document.get(
                "extracted_text",
                "",
            )
        )

        rows = extract_lab_rows_from_document(
            text
        )

        for row in rows:
            if row["test_name"] != "blood glucose":
                continue

            answer = (
                "The patient's documented blood glucose "
                f"was {row['value']}"
            )

            if row.get("unit"):
                answer += f" {row['unit']}"

            if row.get("date"):
                answer += f" on {row['date']}"

            if row.get("reference_range"):
                answer += (
                    " (documented reference range: "
                    f"{row['reference_range']})"
                )

            if document_is_synthetic(
                text
            ):
                answer += (
                    ". The source document is marked "
                    "as synthetic/test data."
                )
            else:
                answer += "."

            return answer

    return None


def deterministic_medication_answer(
    clinical_context: dict,
    question: str,
) -> str | None:
    """Retrieve documented prescriptions when explicitly requested."""
    q = clean_text(
        question
    ).lower()

    if not any(
        term in q
        for term in MEDICATION_TERMS
    ):
        return None

    prescriptions = clinical_context.get(
        "prescriptions",
        [],
    )

    if not prescriptions:
        return (
            "No documented prescriptions or medications "
            "were found in this patient's records."
        )

    lines = [
        "Documented prescriptions in this patient's records:"
    ]

    for prescription in prescriptions:
        number = prescription.get(
            "prescription_number"
        )

        created_at = prescription.get(
            "created_at"
        )

        prefix = "-"

        if number:
            prefix += f" {number}:"
        else:
            prefix += ""

        if created_at:
            prefix += f" {created_at}"

        items = prescription.get(
            "items",
            [],
        )

        if not items:
            lines.append(
                prefix
            )
            continue

        for item in items:
            medicine = clean_text(
                item.get(
                    "medicine_name",
                    "",
                )
            )

            details = []

            for key in (
                "dosage",
                "frequency",
                "duration",
                "route",
                "instructions",
            ):
                value = clean_text(
                    item.get(
                        key,
                        "",
                    )
                )

                if value:
                    details.append(
                        f"{key}: {value}"
                    )

            if details:
                lines.append(
                    f"{prefix} {medicine} "
                    f"({'; '.join(details)})"
                )
            else:
                lines.append(
                    f"{prefix} {medicine}"
                )

    lines.append(
        "This is a retrieval of documented prescriptions; "
        "it is not a medication recommendation."
    )

    return "\n".join(
        lines
    )


def deterministic_diagnosis_answer(
    clinical_context: dict,
    question: str,
) -> str | None:
    """Retrieve explicitly documented diagnoses only."""
    q = clean_text(
        question
    ).lower()

    if not any(
        term in q
        for term in DIAGNOSIS_TERMS
    ):
        return None

    diagnoses = []

    for record in clinical_context.get(
        "medical_records",
        [],
    ):
        diagnosis = clean_text(
            record.get(
                "diagnosis",
                "",
            )
        )

        if diagnosis:
            diagnoses.append(
                {
                    "diagnosis": diagnosis,
                    "date": record.get(
                        "created_at"
                    ),
                }
            )

    if not diagnoses:
        return (
            "No explicitly documented diagnosis was found "
            "in this patient's available medical records."
        )

    lines = [
        "Documented diagnoses/clinical diagnoses:"
    ]

    for item in diagnoses:
        if item["date"]:
            lines.append(
                f"- {item['diagnosis']} "
                f"(recorded {item['date']})"
            )
        else:
            lines.append(
                f"- {item['diagnosis']}"
            )

    return "\n".join(
        lines
    )


# ==========================================================
# Clinical Body / Mannequin Mapping
# ==========================================================

BODY_REGION_RULES = {
    "HEAD": (
        "head",
        "brain",
        "neurolog",
        "migraine",
        "headache",
        "cerebral",
        "cranial",
    ),
    "EYES": (
        "eye",
        "vision",
        "retina",
        "ocular",
        "ophthalm",
    ),
    "EARS": (
        "ear",
        "hearing",
        "otitis",
        "auditory",
    ),
    "HEART": (
        "cardiac",
        "heart",
        "coronary",
        "troponin",
        "qtc",
        "ejection fraction",
        "heart rate",
    ),
    "CHEST": (
        "lung",
        "pulmonary",
        "respiratory",
        "chest",
        "bronch",
        "pneumonia",
        "oxygen saturation",
        "spo2",
        "fev1",
        "chest x-ray",
    ),
    "ABDOMEN": (
        "liver",
        "hepatic",
        "gallbladder",
        "stomach",
        "gastric",
        "intestin",
        "bowel",
        "pancrea",
        "abdomen",
        "abdominal",
    ),
    "KIDNEYS": (
        "kidney",
        "renal",
        "nephro",
        "urinary",
        "urea",
        "creatinine",
    ),
    "BLOOD": (
        "blood",
        "hemoglobin",
        "haemoglobin",
        "anemia",
        "anaemia",
        "platelet",
        "white blood",
        "wbc",
        "rbc",
    ),
    "METABOLIC": (
        "glucose",
        "blood sugar",
        "hba1c",
        "cholesterol",
        "triglyceride",
        "metabolic",
        "diabetes",
    ),
    "MUSCULOSKELETAL": (
        "bone",
        "joint",
        "muscle",
        "orthopedic",
        "orthopaedic",
        "fracture",
        "arthritis",
        "spine",
        "back pain",
    ),
    "SKIN": (
        "skin",
        "dermat",
        "rash",
        "lesion",
        "wound",
        "burn",
    ),
}


def map_text_to_body_regions(
    text: str,
) -> list[str]:
    """
    Map documented terminology to visual body regions.

    This is a UI mapping, not a diagnosis and not a claim that
    the organ itself is diseased.
    """
    lowered = clean_text(
        text
    ).lower()

    regions = []

    for region, keywords in BODY_REGION_RULES.items():
        if any(
            keyword in lowered
            for keyword in keywords
        ):
            regions.append(
                region
            )

    return regions


def build_body_map(
    clinical_context: dict,
    intelligence: dict,
) -> list[dict]:
    """
    Produce frontend-friendly mannequin regions.

    Regions are marked only when supported by documented findings.
    """
    region_data = {
        region: {
            "region": region,
            "status": "NO_DOCUMENTED_FINDING",
            "findings": [],
            "evidence": [],
        }
        for region in BODY_REGION_RULES
    }

    # Lab evidence.
    for finding in intelligence.get(
        "all_findings",
        [],
    ):
        test_name = clean_text(
            finding.get(
                "test_name",
                "",
            )
        )

        regions = map_text_to_body_regions(
            test_name
        )

        for region in regions:
            item = region_data[region]

            item["findings"].append(
                {
                    "type": "laboratory",
                    "test_name": test_name,
                    "value": finding.get(
                        "value"
                    ),
                    "unit": finding.get(
                        "unit"
                    ),
                    "reference_range": finding.get(
                        "reference_range"
                    ),
                    "status": finding.get(
                        "status"
                    ),
                    "date": finding.get(
                        "date"
                    ),
                    "synthetic": finding.get(
                        "synthetic",
                        False,
                    ),
                    "document_id": finding.get(
                        "document_id"
                    ),
                }
            )

            if finding.get(
                "status"
            ) in {
                "ABOVE_STATED_RANGE",
                "BELOW_STATED_RANGE",
            }:
                item["status"] = "ATTENTION"
            elif (
                item["status"]
                == "NO_DOCUMENTED_FINDING"
            ):
                item["status"] = "DOCUMENTED"

            item["evidence"].append(
                {
                    "source": finding.get(
                        "source"
                    ),
                    "document_id": finding.get(
                        "document_id"
                    ),
                    "filename": finding.get(
                        "filename"
                    ),
                }
            )

    # Uploaded clinical documents can contain non-laboratory cardiac,
    # respiratory, imaging, and narrative findings. The previous version
    # only mapped regions from numeric lab test names, so a completed
    # cardiac/respiratory report could be present in clinical_documents
    # while the mannequin remained unchanged.
    for document in clinical_context.get(
        "clinical_documents",
        [],
    ):
        document_text = clean_text(
            document.get(
                "extracted_text",
                "",
            )
        )

        if not document_text:
            continue

        regions = map_text_to_body_regions(
            document_text
        )

        for region in regions:
            item = region_data[region]

            if item["status"] == "NO_DOCUMENTED_FINDING":
                item["status"] = "DOCUMENTED"

            item["evidence"].append(
                {
                    "source": "clinical_document",
                    "document_id": document.get(
                        "document_id"
                    ),
                    "filename": document.get(
                        "filename"
                    ),
                }
            )

            # Surface explicit documented cardiac/respiratory finding
            # statements as evidence without inventing values.
            lowered = document_text.lower()
            for label, pattern in (
                (
                    "cardiac findings",
                    r"documented cardiac findings\s*:\s*([^.;]+(?:\.[^\n]*)?)",
                ),
                (
                    "respiratory findings",
                    r"documented respiratory findings\s*:\s*([^.;]+(?:\.[^\n]*)?)",
                ),
            ):
                match = re.search(
                    pattern,
                    document_text,
                    flags=re.IGNORECASE,
                )

                if match:
                    statement = clean_text(
                        match.group(1)
                    )

                    if statement:
                        item["findings"].append(
                            {
                                "type": "documented_clinical_finding",
                                "test_name": label,
                                "value": statement,
                                "unit": "",
                                "reference_range": "",
                                "status": "DOCUMENTED",
                                "date": extract_report_date(
                                    document_text
                                ),
                                "synthetic": document.get(
                                    "synthetic",
                                    False,
                                ),
                                "document_id": document.get(
                                    "document_id"
                                ),
                            }
                        )

    # Explicitly documented medical record text.
    for record in clinical_context.get(
        "medical_records",
        [],
    ):
        documented_text = " ".join(
            filter(
                None,
                (
                    record.get(
                        "chief_complaint"
                    ),
                    record.get(
                        "history_present_illness"
                    ),
                    record.get(
                        "past_medical_history"
                    ),
                    record.get(
                        "physical_examination"
                    ),
                    record.get(
                        "diagnosis"
                    ),
                    record.get(
                        "notes"
                    ),
                ),
            )
        )

        for region in map_text_to_body_regions(
            documented_text
        ):
            item = region_data[region]

            if item["status"] == "NO_DOCUMENTED_FINDING":
                item["status"] = "DOCUMENTED"

            item["evidence"].append(
                {
                    "source": "medical_record",
                    "record_number": record.get(
                        "record_number"
                    ),
                    "created_at": record.get(
                        "created_at"
                    ),
                }
            )

    # Only return regions that have documented evidence.
    return [
        value
        for value in region_data.values()
        if value["status"]
        != "NO_DOCUMENTED_FINDING"
    ]


# ==========================================================
# Context Builder
# ==========================================================

async def build_patient_context(
    patient_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """
    Build a complete read-only clinical context for one patient.

    Important:
    ignored documents are returned for transparency but are never
    included in clinical evidence sent to Ollama.
    """
    patient = await db.get(
        Patient,
        patient_id,
    )

    if (
        patient is None
        or getattr(
            patient,
            "deleted_at",
            None,
        ) is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    # ------------------------------------------------------
    # Medical records
    # ------------------------------------------------------
    medical_statement = select(
        MedicalRecord
    )
    medical_statement = apply_patient_scope(
        medical_statement,
        MedicalRecord,
        patient_id,
    )

    medical_statement = medical_statement.order_by(
        MedicalRecord.created_at.desc()
    )

    medical_result = await db.execute(
        medical_statement
    )

    medical_records = list(
        medical_result.scalars().all()
    )

    medical_record_data = []

    for record in medical_records:
        medical_record_data.append(
            {
                "record_number": getattr(
                    record,
                    "record_number",
                    None,
                ),
                "chief_complaint": getattr(
                    record,
                    "chief_complaint",
                    None,
                ),
                "history_present_illness": getattr(
                    record,
                    "history_present_illness",
                    None,
                ),
                "past_medical_history": getattr(
                    record,
                    "past_medical_history",
                    None,
                ),
                "family_history": getattr(
                    record,
                    "family_history",
                    None,
                ),
                "allergies": getattr(
                    record,
                    "allergies",
                    None,
                ),
                "current_medications": getattr(
                    record,
                    "current_medications",
                    None,
                ),
                "physical_examination": getattr(
                    record,
                    "physical_examination",
                    None,
                ),
                "diagnosis": getattr(
                    record,
                    "diagnosis",
                    None,
                ),
                "treatment_plan": getattr(
                    record,
                    "treatment_plan",
                    None,
                ),
                "notes": getattr(
                    record,
                    "notes",
                    None,
                ),
                "created_at": serialize_value(
                    getattr(
                        record,
                        "created_at",
                        None,
                    )
                ),
            }
        )

    # ------------------------------------------------------
    # Laboratory tests/results
    # ------------------------------------------------------
    lab_statement = (
        select(
            LabTest,
            LabResult,
        )
        .outerjoin(
            LabResult,
            LabResult.lab_test_id == LabTest.id,
        )
    )

    lab_statement = apply_patient_scope(
        lab_statement,
        LabTest,
        patient_id,
    )

    lab_statement = lab_statement.order_by(
        LabTest.created_at.desc()
    )

    lab_result_query = await db.execute(
        lab_statement
    )

    lab_rows = lab_result_query.all()

    lab_data = []

    for lab_test, lab_result_item in lab_rows:
        result_value = (
            getattr(
                lab_result_item,
                "result",
                None,
            )
            if lab_result_item is not None
            else None
        )

        reference_range = (
            getattr(
                lab_result_item,
                "reference_range",
                None,
            )
            if lab_result_item is not None
            else None
        )

        unit = ""

        if lab_result_item is not None:
            for key in (
                "unit",
                "units",
                "result_unit",
            ):
                candidate = getattr(
                    lab_result_item,
                    key,
                    None,
                )

                if candidate:
                    unit = clean_text(
                        candidate
                    )
                    break

        lab_data.append(
            {
                "test_number": getattr(
                    lab_test,
                    "test_number",
                    None,
                ),
                "test_name": getattr(
                    lab_test,
                    "test_name",
                    None,
                ),
                "status": enum_token(
                    getattr(
                        lab_test,
                        "status",
                        None,
                    ),
                    default="UNKNOWN",
                ),
                "requested_date": serialize_value(
                    getattr(
                        lab_test,
                        "requested_date",
                        None,
                    )
                ),
                "completed_date": serialize_value(
                    getattr(
                        lab_test,
                        "completed_date",
                        None,
                    )
                ),
                "result": (
                    serialize_value(
                        result_value
                    )
                    if result_value is not None
                    else None
                ),
                "unit": unit,
                "reference_range": (
                    clean_text(
                        reference_range
                    )
                    if reference_range is not None
                    else ""
                ),
                "remarks": (
                    getattr(
                        lab_result_item,
                        "remarks",
                        None,
                    )
                    if lab_result_item is not None
                    else None
                ),
            }
        )

    # ------------------------------------------------------
    # Prescriptions
    # ------------------------------------------------------
    prescription_statement = (
        select(Prescription)
        .options(
            selectinload(
                Prescription.items
            )
        )
    )

    prescription_statement = apply_patient_scope(
        prescription_statement,
        Prescription,
        patient_id,
    )

    prescription_statement = prescription_statement.order_by(
        Prescription.created_at.desc()
    )

    prescription_result = await db.execute(
        prescription_statement
    )

    prescriptions = list(
        prescription_result.scalars().unique().all()
    )

    prescription_data = []

    for prescription in prescriptions:
        items = []

        for item in getattr(
            prescription,
            "items",
            [],
        ):
            items.append(
                {
                    "medicine_name": getattr(
                        item,
                        "medicine_name",
                        None,
                    ),
                    "dosage": getattr(
                        item,
                        "dosage",
                        None,
                    ),
                    "frequency": getattr(
                        item,
                        "frequency",
                        None,
                    ),
                    "duration": getattr(
                        item,
                        "duration",
                        None,
                    ),
                    "route": getattr(
                        item,
                        "route",
                        None,
                    ),
                    "instructions": getattr(
                        item,
                        "instructions",
                        None,
                    ),
                    "quantity": getattr(
                        item,
                        "quantity",
                        None,
                    ),
                }
            )

        prescription_data.append(
            {
                "prescription_number": getattr(
                    prescription,
                    "prescription_number",
                    None,
                ),
                "notes": getattr(
                    prescription,
                    "notes",
                    None,
                ),
                "created_at": serialize_value(
                    getattr(
                        prescription,
                        "created_at",
                        None,
                    )
                ),
                "items": items,
            }
        )

    # ------------------------------------------------------
    # Patient documents
    # ------------------------------------------------------
    document_statement = select(
        PatientDocument
    )

    document_statement = apply_patient_scope(
        document_statement,
        PatientDocument,
        patient_id,
    )

    document_statement = document_statement.order_by(
        PatientDocument.created_at.desc()
    )

    document_result = await db.execute(
        document_statement
    )

    documents = list(
        document_result.scalars().all()
    )

    clinical_documents = []
    ignored_documents = []

    for document in documents:
        document_data = document_to_dict(
            document,
            include_text=True,
        )

        if document_is_clinical(
            document
        ):
            clinical_documents.append(
                document_data
            )
        else:
            document_data[
                "ignore_reason"
            ] = (
                "Document is not a completed, "
                "classified clinical document."
            )

            ignored_documents.append(
                document_data
            )

    return {
        "patient": patient_to_dict(
            patient
        ),
        "medical_records": medical_record_data,
        "laboratory": lab_data,
        "prescriptions": prescription_data,
        "clinical_documents": clinical_documents,
        "ignored_documents": ignored_documents,
    }


# ==========================================================
# Ollama
# ==========================================================

async def call_ollama(
    prompt: str,
) -> str:
    """Call the local Ollama HTTP API safely."""
    payload = {
        "model": model_name(),
        "prompt": prompt,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(
            timeout=ollama_timeout()
        ) as client:
            response = await client.post(
                f"{ollama_base_url()}/api/generate",
                json=payload,
            )

            response.raise_for_status()

            result = response.json()

    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Ollama is not reachable. Start Ollama and "
                "make sure the configured model is available."
            ),
        ) from exc

    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Ollama request timed out.",
        ) from exc

    except httpx.HTTPStatusError as exc:
        detail = (
            f"Ollama returned HTTP {exc.response.status_code}."
        )

        try:
            body = exc.response.json()
            if isinstance(body, dict) and body.get("error"):
                detail = (
                    f"Ollama error: {body['error']}"
                )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc

    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama returned invalid JSON.",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Failed to communicate with Ollama."
            ),
        ) from exc

    answer = clean_text(
        result.get(
            "response",
            "",
        )
    )

    if not answer:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama returned an empty response.",
        )

    return answer


def clinical_context_for_ollama(
    clinical_context: dict,
) -> dict:
    """
    Build the strict evidence payload for Ollama.

    ignored_documents are intentionally absent.
    """
    documents = []

    for document in clinical_context.get(
        "clinical_documents",
        [],
    ):
        copied = dict(
            document
        )

        text = clean_text(
            copied.get(
                "extracted_text",
                "",
            )
        )

        copied["extracted_text"] = text[
            :MAX_DOCUMENT_CHARS_FOR_OLLAMA
        ]

        if len(text) > MAX_DOCUMENT_CHARS_FOR_OLLAMA:
            copied["extracted_text_truncated"] = True

        documents.append(
            copied
        )

    evidence = {
        "patient": clinical_context.get(
            "patient",
            {},
        ),
        "medical_records": clinical_context.get(
            "medical_records",
            [],
        ),
        "laboratory": clinical_context.get(
            "laboratory",
            [],
        ),
        "prescriptions": clinical_context.get(
            "prescriptions",
            [],
        ),
        "clinical_documents": documents,
    }

    raw = json.dumps(
        evidence,
        indent=2,
        default=serialize_value,
    )

    if len(raw) <= MAX_TOTAL_CONTEXT_CHARS_FOR_OLLAMA:
        return evidence

    # If the context is unusually large, trim document text first.
    remaining = MAX_TOTAL_CONTEXT_CHARS_FOR_OLLAMA

    trimmed_documents = []

    for document in documents:
        copy = dict(
            document
        )

        text = clean_text(
            copy.get(
                "extracted_text",
                "",
            )
        )

        budget = max(
            1000,
            min(
                len(text),
                remaining // max(
                    1,
                    len(documents),
                ),
            ),
        )

        copy["extracted_text"] = text[
            :budget
        ]

        copy["extracted_text_truncated"] = (
            len(text) > budget
        )

        trimmed_documents.append(
            copy
        )

    evidence["clinical_documents"] = (
        trimmed_documents
    )

    return evidence


# ==========================================================
# Ollama Analysis
# ==========================================================

async def analyze_with_ollama(
    clinical_context: dict,
) -> str:
    """Generate a read-only patient summary."""
    intelligence = build_clinical_intelligence(
        clinical_context
    )

    evidence = clinical_context_for_ollama(
        clinical_context
    )

    prompt = f"""
You are AGCT's clinical information summarization assistant.

Analyze ONE selected patient's documented clinical evidence.

STRICT RULES:
- Use only the supplied evidence.
- Never invent missing values.
- Never invent dates, units, diagnoses, medications, or history.
- Do not diagnose.
- Do not prescribe.
- Do not recommend changing medication.
- Do not treat your response as a replacement for a clinician.
- Only processed/classified clinical_documents are evidence.
- Ignore unrelated/unclassified/pending documents.
- Synthetic/test clinical documents may be used for software testing,
  but clearly label their values as synthetic/test data.
- If a value has an explicit reference range, you may compare the value
  to that stated range.
- Never invent a reference range.
- Never turn an out-of-range result into a diagnosis.

The backend has already performed deterministic laboratory comparisons:

{json.dumps(
    intelligence,
    indent=2,
    default=serialize_value,
)}

Return these sections:

PATIENT SUMMARY
CLINICAL HISTORY
LABORATORY FINDINGS
MEDICATIONS
DOCUMENT FINDINGS
POSSIBLE CLINICAL CONCERNS
IMPORTANT MISSING INFORMATION
SUGGESTED FOLLOW-UP
DISCLAIMER

For follow-up:
- describe evidence that deserves professional review
- do not prescribe or alter treatment
- do not diagnose
- do not imply certainty beyond the records

PATIENT CLINICAL EVIDENCE:

{json.dumps(
    evidence,
    indent=2,
    default=serialize_value,
)}
"""

    return await call_ollama(
        prompt
    )


# ==========================================================
# Ollama Chat
# ==========================================================

async def ask_digital_twin_ollama(
    clinical_context: dict,
    question: str,
) -> str:
    """
    Answer a doctor's question.

    Deterministic retrieval is attempted first for high-value factual
    questions. Ollama is used only when summarization/reasoning is needed.
    """
    if question_requests_clinical_suggestions(
        question
    ):
        deterministic = format_clinical_suggestions(
            clinical_context
        )

        if deterministic:
            return deterministic

    deterministic = deterministic_glucose_answer(
        clinical_context,
        question,
    )

    if deterministic:
        return deterministic

    deterministic = deterministic_medication_answer(
        clinical_context,
        question,
    )

    if deterministic:
        return deterministic

    deterministic = deterministic_diagnosis_answer(
        clinical_context,
        question,
    )

    if deterministic:
        return deterministic

    evidence = clinical_context_for_ollama(
        clinical_context
    )

    intelligence = build_clinical_intelligence(
        clinical_context
    )

    prompt = f"""
You are AGCT's patient-specific clinical information retrieval assistant.

You are answering a doctor about ONE selected patient.

Use ONLY the supplied CLINICAL EVIDENCE.

Never:
- invent a value
- invent a date
- invent a unit
- invent a diagnosis
- invent a medication
- use another patient's information
- use ignored/unclassified documents
- prescribe medication
- recommend changing medication
- make an unsupported diagnosis

If the requested information is absent, say exactly:
"{NO_DOCUMENTED_VALUE}"

If a documented value is present, report it directly.

Synthetic/test rule:
A processed clinical document explicitly marked synthetic/fictional/sample
is still valid evidence for software testing. Report its documented values,
and clearly say that the source is synthetic/test data.

Laboratory rule:
- "blood sugar" and "blood glucose" may refer to the same explicitly
  documented glucose result.
- Preserve the exact unit from the source.
- Preserve the source date when available.
- Do not confuse a result with its reference range.
- Do not invent a reference range.
- Do not turn an out-of-range result into a diagnosis.

For questions asking about abnormal findings or follow-up, rely on the
backend's deterministic evidence summary below.

DETERMINISTIC CLINICAL INTELLIGENCE:

{json.dumps(
    intelligence,
    indent=2,
    default=serialize_value,
)}

DOCTOR QUESTION:

{question}

CLINICAL EVIDENCE:

{json.dumps(
    evidence,
    indent=2,
    default=serialize_value,
)}

Answer directly and concisely.
"""

    return await call_ollama(
        prompt
    )


# ==========================================================
# Dashboard Data Builders
# ==========================================================

def _condition_key(value: str) -> str:
    """
    Normalize a condition name for safe deduplication.
    """
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        clean_text(value).lower(),
    ).strip()


def _extract_explicit_conditions_from_text(
    text: str,
) -> list[str]:
    """
    Extract explicitly documented diagnoses/conditions from
    clinical document text.

    IMPORTANT:
    - This function does NOT infer diagnoses from laboratory values.
    - It only extracts text that is explicitly presented as a
      diagnosis/condition/impression/history.
    """

    normalized = clean_text(text)

    if not normalized:
        return []

    conditions: list[str] = []

    # ------------------------------------------------------
    # Explicit labelled clinical sections
    # ------------------------------------------------------

    labelled_patterns = (
        r"(?:diagnosis|diagnoses)\s*[:\-]\s*([^.;\n]+)",
        r"(?:final\s+diagnosis)\s*[:\-]\s*([^.;\n]+)",
        r"(?:discharge\s+diagnosis)\s*[:\-]\s*([^.;\n]+)",
        r"(?:clinical\s+diagnosis)\s*[:\-]\s*([^.;\n]+)",
        r"(?:clinical\s+impression)\s*[:\-]\s*([^.;\n]+)",
        r"(?:impression)\s*[:\-]\s*([^.;\n]+)",
        r"(?:assessment)\s*[:\-]\s*([^.;\n]+)",
        r"(?:assessment\s*/\s*plan)\s*[:\-]\s*([^.;\n]+)",
        r"(?:past\s+medical\s+history)\s*[:\-]\s*([^.;\n]+)",
        r"(?:medical\s+history)\s*[:\-]\s*([^.;\n]+)",
        r"(?:known\s+conditions?)\s*[:\-]\s*([^.;\n]+)",
        r"(?:chronic\s+conditions?)\s*[:\-]\s*([^.;\n]+)",
        r"(?:active\s+conditions?)\s*[:\-]\s*([^.;\n]+)",
        r"(?:problem\s+list)\s*[:\-]\s*([^.;\n]+)",
    )

    for pattern in labelled_patterns:

        matches = re.finditer(
            pattern,
            normalized,
            flags=re.IGNORECASE,
        )

        for match in matches:

            value = clean_text(
                match.group(1)
            )

            if not value:
                continue

            # Remove common non-condition continuation text.
            value = re.split(
                r"\b(?:treatment|plan|medication|medications|follow[- ]?up)\b",
                value,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0]

            # Split lists such as:
            # Hypertension, Dyslipidemia, Diabetes
            parts = re.split(
                r"\s*(?:,|;|\||\band\b)\s*",
                value,
                flags=re.IGNORECASE,
            )

            for part in parts:

                condition = clean_text(
                    part
                )

                if not condition:
                    continue

                conditions.append(
                    condition
                )

    # ------------------------------------------------------
    # Bullet-style diagnosis lines
    # ------------------------------------------------------

    for line in str(text).splitlines():

        line_clean = clean_text(
            line
        )

        if not line_clean:
            continue

        match = re.match(
            r"^(?:[-•*]\s*)?"
            r"(?:diagnosis|diagnoses|"
            r"discharge diagnosis|"
            r"clinical impression|"
            r"impression|"
            r"assessment)"
            r"\s*[:\-]\s*(.+)$",
            line_clean,
            flags=re.IGNORECASE,
        )

        if match:

            value = clean_text(
                match.group(1)
            )

            if value:
                parts = re.split(
                    r"\s*(?:,|;|\band\b)\s*",
                    value,
                    flags=re.IGNORECASE,
                )

                for part in parts:

                    condition = clean_text(
                        part
                    )

                    if condition:
                        conditions.append(
                            condition
                        )

    # ------------------------------------------------------
    # Clean extracted values
    # ------------------------------------------------------

    cleaned: list[str] = []

    ignored_phrases = {
        "none",
        "nil",
        "not documented",
        "not available",
        "no diagnosis",
        "no known conditions",
        "no known medical conditions",
        "normal",
    }

    for condition in conditions:

        condition = clean_text(
            condition
        )

        if not condition:
            continue

        if condition.lower() in ignored_phrases:
            continue

        # Avoid huge paragraph fragments.
        if len(condition) > 180:
            continue

        # Remove trailing punctuation.
        condition = condition.rstrip(
            ".,;:-"
        ).strip()

        if not condition:
            continue

        cleaned.append(
            condition
        )

    return cleaned


def build_conditions(
    clinical_context: dict,
) -> list[dict]:
    """
    Build explicitly documented patient conditions.

    Sources:
      1. MedicalRecord.diagnosis
      2. Processed/classified clinical documents

    IMPORTANT:
      Abnormal laboratory results are NOT converted into diagnoses.
      A condition only enters this list when it is explicitly
      documented in a medical record or labelled clinical-document
      section such as Diagnosis, Impression, Assessment, etc.
    """

    conditions: list[dict] = []

    seen: set[str] = set()

    # ======================================================
    # 1. Existing structured medical-record diagnoses
    # ======================================================

    for record in clinical_context.get(
        "medical_records",
        [],
    ):

        diagnosis = clean_text(
            record.get(
                "diagnosis",
                "",
            )
        )

        if not diagnosis:
            continue

        # A record may contain multiple diagnoses.
        parts = re.split(
            r"\s*(?:,|;|\||\band\b)\s*",
            diagnosis,
            flags=re.IGNORECASE,
        )

        for part in parts:

            condition = clean_text(
                part
            )

            if not condition:
                continue

            key = _condition_key(
                condition
            )

            if not key or key in seen:
                continue

            seen.add(key)

            conditions.append(
                {
                    "name": condition,
                    "source": "medical_record",
                    "record_number": record.get(
                        "record_number"
                    ),
                    "date": record.get(
                        "created_at"
                    ),
                    "documented": True,
                    "synthetic": False,
                }
            )

    # ======================================================
    # 2. Explicit conditions inside uploaded documents
    # ======================================================

    for document in clinical_context.get(
        "clinical_documents",
        [],
    ):

        text = clean_text(
            document.get(
                "extracted_text",
                "",
            )
        )

        if not text:
            continue

        extracted_conditions = (
            _extract_explicit_conditions_from_text(
                text
            )
        )

        for condition in extracted_conditions:

            key = _condition_key(
                condition
            )

            if not key or key in seen:
                continue

            seen.add(key)

            report_date = (
                extract_report_date(
                    text
                )
                or document.get(
                    "created_at"
                )
            )

            conditions.append(
                {
                    "name": condition,
                    "source": "clinical_document",
                    "document_id": document.get(
                        "document_id"
                    ),
                    "filename": document.get(
                        "filename"
                    ),
                    "document_type": document.get(
                        "document_type"
                    ),
                    "date": report_date,
                    "documented": True,
                    "synthetic": document.get(
                        "synthetic",
                        False,
                    ),
                }
            )

    # ======================================================
    # Sort newest documented conditions first
    # ======================================================

    conditions.sort(
        key=lambda item: parse_date_for_sort(
            item.get(
                "date"
            )
        )
    )

    return conditions


def build_alerts(
    clinical_context: dict,
) -> list[dict]:
    """
    Build review alerts from documented evidence.

    These are evidence-review alerts, not emergency/criticality scores.
    """
    intelligence = build_clinical_intelligence(
        clinical_context
    )

    alerts = []

    for finding in intelligence.get(
        "abnormal_findings",
        [],
    ):
        direction = (
            "above"
            if finding["status"]
            == "ABOVE_STATED_RANGE"
            else "below"
        )

        severity = "REVIEW"

        alerts.append(
            {
                "type": "LABORATORY_REVIEW",
                "severity": severity,
                "title": (
                    f"{finding['test_name']} "
                    f"{direction} stated range"
                ),
                "message": (
                    f"{finding['value']}"
                    + (
                        f" {finding['unit']}"
                        if finding.get("unit")
                        else ""
                    )
                    + f" vs stated range "
                    f"{finding.get('reference_range') or 'not specified'}."
                ),
                "date": finding.get(
                    "date"
                ),
                "document_id": finding.get(
                    "document_id"
                ),
                "filename": finding.get(
                    "filename"
                ),
                "synthetic": finding.get(
                    "synthetic",
                    False,
                ),
            }
        )

    return alerts


def build_timeline(
    clinical_context: dict,
) -> list[dict]:
    """Build a chronological view of documented patient events."""
    events = []

    for record in clinical_context.get(
        "medical_records",
        [],
    ):
        events.append(
            {
                "type": "MEDICAL_RECORD",
                "date": record.get(
                    "created_at"
                ),
                "title": (
                    "Medical record"
                ),
                "description": (
                    record.get(
                        "chief_complaint"
                    )
                    or record.get(
                        "diagnosis"
                    )
                    or "Medical record documented."
                ),
                "source": "medical_record",
                "record_number": record.get(
                    "record_number"
                ),
            }
        )

    for lab in clinical_context.get(
        "laboratory",
        [],
    ):
        lab_date = (
            lab.get(
                "completed_date"
            )
            or lab.get(
                "requested_date"
            )
        )

        events.append(
            {
                "type": "LABORATORY",
                "date": lab_date,
                "title": (
                    lab.get(
                        "test_name"
                    )
                    or "Laboratory test"
                ),
                "description": (
                    f"Result: {lab.get('result')}"
                    + (
                        f" {lab.get('unit')}"
                        if lab.get("unit")
                        else ""
                    )
                ),
                "source": "laboratory",
                "test_number": lab.get(
                    "test_number"
                ),
                "reference_range": lab.get(
                    "reference_range"
                ),
            }
        )

    for prescription in clinical_context.get(
        "prescriptions",
        [],
    ):
        events.append(
            {
                "type": "PRESCRIPTION",
                "date": prescription.get(
                    "created_at"
                ),
                "title": (
                    "Prescription"
                ),
                "description": (
                    prescription.get(
                        "prescription_number"
                    )
                    or "Prescription documented."
                ),
                "source": "prescription",
                "prescription_number": prescription.get(
                    "prescription_number"
                ),
            }
        )

    for document in clinical_context.get(
        "clinical_documents",
        [],
    ):
        report_date = extract_report_date(
            document.get(
                "extracted_text",
                "",
            )
        )

        event_date = (
            report_date
            or document.get(
                "created_at"
            )
        )

        events.append(
            {
                "type": "CLINICAL_DOCUMENT",
                "date": event_date,
                "title": (
                    document.get(
                        "filename"
                    )
                    or "Clinical document"
                ),
                "description": (
                    document.get(
                        "document_type"
                    )
                    or "Clinical document"
                ),
                "source": "clinical_document",
                "document_id": document.get(
                    "document_id"
                ),
                "document_type": document.get(
                    "document_type"
                ),
                "synthetic": document.get(
                    "synthetic",
                    False,
                ),
            }
        )

    events.sort(
        key=lambda item: parse_date_for_sort(
            item.get(
                "date"
            )
        )
    )

    return events


def build_findings_payload(
    clinical_context: dict,
) -> dict:
    intelligence = build_clinical_intelligence(
        clinical_context
    )

    return {
        "findings": intelligence[
            "all_findings"
        ],
        "abnormal_findings": intelligence[
            "abnormal_findings"
        ],
        "unknown_reference_findings": intelligence[
            "unknown_reference_findings"
        ],
    }


def build_overview_payload(
    clinical_context: dict,
) -> dict:
    intelligence = build_clinical_intelligence(
        clinical_context
    )

    alerts = build_alerts(
        clinical_context
    )

    patient = clinical_context[
        "patient"
    ]

    return {
        "patient": patient,
        "patient_display": {
            "patient_number": patient.get(
                "patient_number"
            ),
            "name": " ".join(
                filter(
                    None,
                    (
                        patient.get(
                            "first_name"
                        ),
                        patient.get(
                            "last_name"
                        ),
                    ),
                )
            ),
            "gender": patient.get(
                "gender"
            ),
            "date_of_birth": patient.get(
                "date_of_birth"
            ),
        },
        "documented_conditions": build_conditions(
            clinical_context
        ),
        "summary_counts": {
            "medical_records": len(
                clinical_context[
                    "medical_records"
                ]
            ),
            "laboratory_tests": len(
                clinical_context[
                    "laboratory"
                ]
            ),
            "prescriptions": len(
                clinical_context[
                    "prescriptions"
                ]
            ),
            "clinical_documents": len(
                clinical_context[
                    "clinical_documents"
                ]
            ),
            "ignored_documents": len(
                clinical_context[
                    "ignored_documents"
                ]
            ),
            "abnormal_lab_findings": len(
                intelligence[
                    "abnormal_findings"
                ]
            ),
            "review_alerts": len(
                alerts
            ),
        },
        "status": (
            "ATTENTION_REQUIRED"
            if alerts
            else "NO_DOCUMENTED_LAB_REVIEW_ALERTS"
        ),
        "latest_events": build_timeline(
            clinical_context
        )[-10:],
        "disclaimer": DISCLAIMER,
    }


def build_dashboard_payload(
    clinical_context: dict,
) -> dict:
    """Single response for the main Digital Twin frontend."""
    intelligence = build_clinical_intelligence(
        clinical_context
    )

    alerts = build_alerts(
        clinical_context
    )

    return {
        **build_overview_payload(
            clinical_context
        ),
        "findings": intelligence[
            "all_findings"
        ],
        "abnormal_findings": intelligence[
            "abnormal_findings"
        ],
        "unknown_reference_findings": intelligence[
            "unknown_reference_findings"
        ],
        "suggested_follow_up": intelligence[
            "suggested_follow_up"
        ],
        "body_map": build_body_map(
            clinical_context,
            intelligence,
        ),
        "alerts": alerts,
        "timeline": build_timeline(
            clinical_context
        ),
        "clinical_documents": [
            {
                key: value
                for key, value in document.items()
                if key != "extracted_text"
            }
            for document in clinical_context.get(
                "clinical_documents",
                [],
            )
        ],
        "ignored_documents": [
            {
                key: value
                for key, value in document.items()
                if key != "extracted_text"
            }
            for document in clinical_context.get(
                "ignored_documents",
                [],
            )
        ],
        "model": model_name(),
        "data_version": datetime.utcnow().isoformat(),
        "disclaimer": DISCLAIMER,
    }


# ==========================================================
# API Endpoints
# ==========================================================

@router.get(
    "/status",
)
async def digital_twin_status(
    current_user: User = Depends(
        DoctorOnly
    ),
):
    """
    Check whether the configured local Ollama server is reachable.
    """
    url = ollama_base_url()

    try:
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            response = await client.get(
                f"{url}/api/tags"
            )
            response.raise_for_status()
            data = response.json()

        models = [
            item.get(
                "name"
            )
            for item in data.get(
                "models",
                []
            )
            if item.get(
                "name"
            )
        ]

        configured_model = model_name()

        return {
            "ollama": "ONLINE",
            "base_url": url,
            "model": configured_model,
            "model_available": (
                configured_model in models
                or any(
                    name.split(":")[0]
                    == configured_model.split(":")[0]
                    for name in models
                )
            ),
            "available_models": models,
        }

    except Exception:
        return {
            "ollama": "OFFLINE",
            "base_url": url,
            "model": model_name(),
            "model_available": False,
            "available_models": [],
        }


@router.get(
    "/{patient_id}/overview",
)
async def get_patient_overview(
    patient_id: uuid.UUID,
    current_user: User = Depends(
        DoctorOnly
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    """Return the frontend-ready patient Digital Twin overview."""
    context = await build_patient_context(
        patient_id,
        db,
    )

    return build_overview_payload(
        context
    )


@router.get(
    "/{patient_id}/findings",
)
async def get_patient_findings(
    patient_id: uuid.UUID,
    current_user: User = Depends(
        DoctorOnly
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    """Return deterministic laboratory findings."""
    context = await build_patient_context(
        patient_id,
        db,
    )

    intelligence = build_clinical_intelligence(
        context
    )

    return {
        "patient_id": str(
            patient_id
        ),
        "patient_number": context[
            "patient"
        ].get(
            "patient_number"
        ),
        **build_findings_payload(
            context
        ),
        "clinical_documents_used": len(
            context[
                "clinical_documents"
            ]
        ),
        "ignored_documents": len(
            context[
                "ignored_documents"
            ]
        ),
        "disclaimer": DISCLAIMER,
    }


@router.get(
    "/{patient_id}/alerts",
)
async def get_patient_alerts(
    patient_id: uuid.UUID,
    current_user: User = Depends(
        DoctorOnly
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    """Return evidence-review alerts."""
    context = await build_patient_context(
        patient_id,
        db,
    )

    return {
        "patient_id": str(
            patient_id
        ),
        "patient_number": context[
            "patient"
        ].get(
            "patient_number"
        ),
        "alerts": build_alerts(
            context
        ),
        "disclaimer": DISCLAIMER,
    }


@router.get(
    "/{patient_id}/timeline",
)
async def get_patient_timeline(
    patient_id: uuid.UUID,
    current_user: User = Depends(
        DoctorOnly
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    """Return the patient's documented clinical timeline."""
    context = await build_patient_context(
        patient_id,
        db,
    )

    return {
        "patient_id": str(
            patient_id
        ),
        "patient_number": context[
            "patient"
        ].get(
            "patient_number"
        ),
        "timeline": build_timeline(
            context
        ),
    }


@router.get(
    "/{patient_id}/body-map",
)
async def get_patient_body_map(
    patient_id: uuid.UUID,
    current_user: User = Depends(
        DoctorOnly
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    """
    Return visual mannequin/body-region data.

    The frontend can use these region keys to highlight a 3D mannequin.
    """
    context = await build_patient_context(
        patient_id,
        db,
    )

    intelligence = build_clinical_intelligence(
        context
    )

    return {
        "patient_id": str(
            patient_id
        ),
        "patient_number": context[
            "patient"
        ].get(
            "patient_number"
        ),
        "body_map": build_body_map(
            context,
            intelligence,
        ),
        "disclaimer": (
            "Body-region highlighting is a visualization of "
            "documented terminology/findings. It is not a "
            "diagnosis or claim that an organ is diseased."
        ),
    }


@router.get(
    "/{patient_id}/dashboard",
)
async def get_patient_dashboard(
    patient_id: uuid.UUID,
    current_user: User = Depends(
        DoctorOnly
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    """
    Single-call Digital Twin dashboard payload.

    This is the endpoint the frontend can use initially to avoid
    making many separate requests.
    """
    context = await build_patient_context(
        patient_id,
        db,
    )

    return build_dashboard_payload(
        context
    )


@router.post(
    "/{patient_id}/analyze",
)
async def analyze_patient_digital_twin(
    patient_id: uuid.UUID,
    request: DigitalTwinAnalyzeRequest | None = None,
    current_user: User = Depends(
        DoctorOnly
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    """
    Refresh the selected patient's Digital Twin evidence.

    IMPORTANT PERFORMANCE FIX
    --------------------------
    This endpoint now returns the deterministic patient evidence immediately.
    It no longer blocks the document-upload pipeline on Ollama.

    Existing frontend calls that POST ``{}`` continue to work because
    ``run_ai`` defaults to False.

    If a caller explicitly sends ``{"run_ai": true}``, the endpoint also
    requests the slower Ollama narrative analysis.
    """

    context = await build_patient_context(
        patient_id,
        db,
    )

    # Build the complete deterministic dashboard first. This is the actual
    # persisted Digital Twin evidence and must never depend on Ollama.
    dashboard = build_dashboard_payload(
        context
    )

    intelligence = build_clinical_intelligence(
        context
    )

    clinical_document_count = len(
        context[
            "clinical_documents"
        ]
    )

    ignored_document_count = len(
        context[
            "ignored_documents"
        ]
    )

    total_document_count = (
        clinical_document_count
        + ignored_document_count
    )

    run_ai = bool(
        request.run_ai
        if request is not None
        else False
    )

    analysis = None
    analysis_status = "NOT_REQUESTED"

    if run_ai:
        try:
            analysis = await analyze_with_ollama(
                context
            )
            analysis_status = "COMPLETED"
        except HTTPException:
            # The deterministic evidence is still valid even when Ollama
            # is unavailable or times out. Do not discard it.
            analysis_status = "FAILED"

    return {
        # --------------------------------------------------
        # Patient identity
        # --------------------------------------------------
        "patient_id": str(
            patient_id
        ),
        "patient_number": context[
            "patient"
        ].get(
            "patient_number"
        ),

        # --------------------------------------------------
        # Deterministic Digital Twin payload
        # --------------------------------------------------
        **dashboard,

        # --------------------------------------------------
        # Backward-compatible fields used by existing frontend code
        # --------------------------------------------------
        "analysis": analysis,
        "analysis_status": analysis_status,

        "clinical_intelligence": {
            "findings": intelligence[
                "all_findings"
            ],
            "abnormal_findings": intelligence[
                "abnormal_findings"
            ],
            "unknown_reference_findings": intelligence[
                "unknown_reference_findings"
            ],
            "suggested_follow_up": intelligence[
                "suggested_follow_up"
            ],
        },

        "data_sources": {
            "medical_records": len(
                context[
                    "medical_records"
                ]
            ),
            "laboratory_tests": len(
                context[
                    "laboratory"
                ]
            ),
            "prescriptions": len(
                context[
                    "prescriptions"
                ]
            ),
            "documents": total_document_count,
            "clinical_documents": clinical_document_count,
            "ignored_documents": ignored_document_count,
        },

        "document_intelligence": {
            "clinical_document_types": sorted(
                CLINICAL_DOCUMENT_TYPES
            ),
            "clinical_documents_used": clinical_document_count,
            "documents_excluded": ignored_document_count,
        },

        "model": model_name(),
        "disclaimer": DISCLAIMER,
    }


@router.post(
    "/{patient_id}/ai-analysis",
)
async def get_patient_ai_analysis(
    patient_id: uuid.UUID,
    current_user: User = Depends(
        DoctorOnly
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    """
    Explicitly run the slower Ollama narrative analysis.

    The normal Digital Twin refresh does not call this endpoint, so document
    uploads remain fast and deterministic.
    """

    context = await build_patient_context(
        patient_id,
        db,
    )

    analysis = await analyze_with_ollama(
        context
    )

    return {
        "patient_id": str(
            patient_id
        ),
        "patient_number": context[
            "patient"
        ].get(
            "patient_number"
        ),
        "analysis": analysis,
        "model": model_name(),
        "data_sources": {
            "medical_records": len(
                context["medical_records"]
            ),
            "laboratory_tests": len(
                context["laboratory"]
            ),
            "prescriptions": len(
                context["prescriptions"]
            ),
            "clinical_documents": len(
                context["clinical_documents"]
            ),
            "ignored_documents": len(
                context["ignored_documents"]
            ),
        },
        "disclaimer": DISCLAIMER,
    }


@router.post(
    "/{patient_id}/clinical-suggestions",
)
async def get_patient_clinical_suggestions(
    patient_id: uuid.UUID,
    current_user: User = Depends(
        DoctorOnly
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    """
    Return deterministic findings and safe evidence-review follow-up.
    """
    context = await build_patient_context(
        patient_id,
        db,
    )

    intelligence = build_clinical_intelligence(
        context
    )

    return {
        "patient_id": str(
            patient_id
        ),
        "patient_number": context[
            "patient"
        ].get(
            "patient_number"
        ),
        "findings": intelligence[
            "all_findings"
        ],
        "abnormal_findings": intelligence[
            "abnormal_findings"
        ],
        "unknown_reference_findings": intelligence[
            "unknown_reference_findings"
        ],
        "suggested_follow_up": intelligence[
            "suggested_follow_up"
        ],
        "clinical_documents_used": len(
            context[
                "clinical_documents"
            ]
        ),
        "ignored_documents": len(
            context[
                "ignored_documents"
            ]
        ),
        "disclaimer": DISCLAIMER,
    }


@router.post(
    "/{patient_id}/chat",
)
async def ask_patient_digital_twin(
    patient_id: uuid.UUID,
    request: DigitalTwinChatRequest,
    current_user: User = Depends(
        DoctorOnly
    ),
    db: AsyncSession = Depends(
        get_db
    ),
):
    """
    Patient-specific AI chat.

    The doctor selects a patient in the frontend. The frontend keeps the
    UUID internally and sends it here; the doctor never needs to type it.
    """
    question = clean_text(
        request.question
    )

    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be empty.",
        )

    context = await build_patient_context(
        patient_id,
        db,
    )

    answer = await ask_digital_twin_ollama(
        context,
        question,
    )

    return {
        "patient_id": str(
            patient_id
        ),
        "patient_number": context[
            "patient"
        ].get(
            "patient_number"
        ),
        "question": question,
        "answer": answer,
        "data_sources": {
            "medical_records": len(
                context[
                    "medical_records"
                ]
            ),
            "laboratory_tests": len(
                context[
                    "laboratory"
                ]
            ),
            "prescriptions": len(
                context[
                    "prescriptions"
                ]
            ),
            "clinical_documents": len(
                context[
                    "clinical_documents"
                ]
            ),
            "ignored_documents": len(
                context[
                    "ignored_documents"
                ]
            ),
        },
        "model": model_name(),
        "disclaimer": DISCLAIMER,
    }