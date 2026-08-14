"""
AGCT Document Classifier

Classifies processed patient documents.

Pipeline:

    UPLOAD
       ↓
    DOCUMENT PROCESSOR
       ↓
    extracted_text
       ↓
    DOCUMENT CLASSIFIER
       ↓
    document_type
       ↓
    DIGITAL TWIN

The classifier:
- Reads extracted text
- Uses local Ollama
- Stores document_type
- Can be called automatically by the document processor
- Can also be called manually through the API
- Does not diagnose patients
"""

from __future__ import annotations

import json
import uuid

import httpx

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import DoctorOnly
from app.database.session import get_db
from app.modules.auth.models import User
from app.modules.patients.documents import PatientDocument


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/document-classification",
    tags=["Document Classification"],
)


# ==========================================================
# Types
# ==========================================================

ALLOWED_DOCUMENT_TYPES = {
    "LAB_REPORT",
    "PRESCRIPTION",
    "MEDICAL_REPORT",
    "IMAGING_REPORT",
    "DISCHARGE_SUMMARY",
    "OTHER",
}


# ==========================================================
# Ollama Configuration
# ==========================================================

def classifier_model() -> str:
    return (
        getattr(
            settings,
            "DEFAULT_CHAT_MODEL",
            None,
        )
        or "llama3.2:3b"
    )


def classifier_ollama_url() -> str:
    return (
        getattr(
            settings,
            "OLLAMA_BASE_URL",
            None,
        )
        or "http://127.0.0.1:11434"
    ).rstrip("/")


# ==========================================================
# Ollama Classification
# ==========================================================

async def classify_with_ollama(
    extracted_text: str,
) -> str:
    """
    Classify extracted medical document text.

    Returns exactly one allowed document type.
    """

    text = (
        extracted_text or ""
    ).strip()

    if not text:
        return "OTHER"

    model = classifier_model()
    base_url = classifier_ollama_url()

    prompt = f"""
You are AGCT's medical document classification system.

Classify the document into EXACTLY ONE of these values:

LAB_REPORT
PRESCRIPTION
MEDICAL_REPORT
IMAGING_REPORT
DISCHARGE_SUMMARY
OTHER

Return JSON only:

{{
  "document_type": "LAB_REPORT"
}}

Rules:

LAB_REPORT:
- Blood tests
- Urine tests
- Biochemistry
- Hematology
- Lipid profiles
- Glucose reports
- HbA1c
- Cardiac laboratory biomarkers
- Respiratory laboratory biomarkers
- Pathology/laboratory results
- Any document primarily containing laboratory measurements

PRESCRIPTION:
- Medication prescriptions
- Medicine instructions
- Dosage/frequency instructions
- Prescription medication lists

MEDICAL_REPORT:
- Clinical consultation
- Physician assessment
- Diagnosis/assessment documentation
- General medical reports

IMAGING_REPORT:
- X-ray
- CT
- MRI
- Ultrasound
- PET
- Echocardiography
- ECG/EKG
- Other diagnostic imaging reports

DISCHARGE_SUMMARY:
- Hospital admission summary
- Hospital discharge summary
- Discharge diagnosis
- Hospital course
- Discharge instructions

OTHER:
- Anything unrelated to clinical medical documentation

Important:
- Classify based on the actual document text.
- Do not diagnose the patient.
- Do not modify values.
- Do not invent missing information.
- Return JSON only.

DOCUMENT:

{text}
"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    try:

        async with httpx.AsyncClient(
            timeout=120.0,
        ) as client:

            response = await client.post(
                f"{base_url}/api/generate",
                json=payload,
            )

            response.raise_for_status()

            result = response.json()

    except httpx.ConnectError as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama is not reachable.",
        ) from exc

    except httpx.TimeoutException as exc:

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Document classification timed out.",
        ) from exc

    except httpx.HTTPStatusError as exc:

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Ollama returned an error: "
                f"{exc.response.text}"
            ),
        ) from exc

    raw_response = (
        result.get(
            "response",
            "",
        )
        or ""
    ).strip()

    if not raw_response:

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama returned an empty classification.",
        )

    try:

        parsed = json.loads(
            raw_response,
        )

    except json.JSONDecodeError as exc:

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Ollama returned invalid classification JSON."
            ),
        ) from exc

    document_type = str(
        parsed.get(
            "document_type",
            "OTHER",
        )
    ).upper().strip()

    if (
        document_type
        not in ALLOWED_DOCUMENT_TYPES
    ):
        document_type = "OTHER"

    return document_type


# ==========================================================
# DATABASE CLASSIFICATION
# ==========================================================

async def classify_document_record(
    document: PatientDocument,
) -> str:
    """
    Classify an already-processed PatientDocument.

    This function is intentionally separated from the HTTP endpoint.

    The document processor can call this directly after extraction:

        extracted_text
            ↓
        COMPLETED
            ↓
        classify_document_record()
            ↓
        document_type
    """

    extracted_text = (
        document.extracted_text or ""
    ).strip()

    if not extracted_text:

        raise ValueError(
            "Cannot classify document without extracted text."
        )

    document_type = await classify_with_ollama(
        extracted_text,
    )

    document.document_type = (
        document_type
    )

    return document_type


# ==========================================================
# MANUAL/API CLASSIFICATION
# ==========================================================

@router.post(
    "/{document_id}/classify",
)
async def classify_document(
    document_id: uuid.UUID,
    current_user: User = Depends(
        DoctorOnly,
    ),
    db: AsyncSession = Depends(
        get_db,
    ),
):
    """
    Manually classify one processed document.

    This endpoint remains available for:
    - Reclassification
    - Repairing old documents
    - Testing
    - Administrative workflows
    """

    document = await db.get(
        PatientDocument,
        document_id,
    )

    if (
        document is None
        or document.deleted_at is not None
    ):

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if not document.extracted_text:

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Document has no extracted text. "
                "Process the document first."
            ),
        )

    document_type = await classify_document_record(
        document,
    )

    await db.commit()

    await db.refresh(
        document,
    )

    return {
        "message": (
            "Document classified successfully."
        ),
        "document_id": str(
            document.id,
        ),
        "patient_id": str(
            document.patient_id,
        ),
        "filename": (
            document.original_filename,
        ),
        "document_type": (
            document.document_type,
        ),
        "processing_status": (
            document.processing_status,
        ),
        "extracted_text_length": len(
            document.extracted_text or "",
        ),
        "model": classifier_model(),
    }