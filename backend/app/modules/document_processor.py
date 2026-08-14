"""
AGCT Document Processor

Automatic upload pipeline:

    PENDING
       ↓
    PROCESSING
       ↓
    TEXT EXTRACTION
       ↓
    DOCUMENT CLASSIFICATION (Ollama)
       ↓
    COMPLETED + document_type

If extraction or classification fails:

    PROCESSING → FAILED

The upload endpoint only creates the database record and queues this
worker after commit. This module owns the complete processing pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)
from PIL import Image
import pytesseract
from pypdf import PdfReader
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DoctorOnly
from app.database.session import (
    AsyncSessionLocal,
    get_db,
)
from app.modules.auth.models import User
from app.modules.patients.documents import PatientDocument
from app.modules.patients.models import Patient


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/document-processing",
    tags=["Document Processing"],
)


# ==========================================================
# TEXT EXTRACTION
# ==========================================================

def extract_pdf_text(
    file_path: Path,
) -> str:
    reader = PdfReader(
        str(file_path),
    )

    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            cleaned = text.strip()

            if cleaned:
                pages.append(cleaned)

    return "\n\n".join(
        pages
    ).strip()


def extract_image_text(
    file_path: Path,
) -> str:
    image = Image.open(
        file_path,
    )

    try:
        return pytesseract.image_to_string(
            image,
        ).strip()
    finally:
        image.close()


def extract_document_text(
    document: PatientDocument,
) -> str:
    file_path = Path(
        document.file_path,
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Document file not found: {file_path}"
        )

    content_type = (
        document.content_type or ""
    ).lower()

    if content_type == "application/pdf":
        return extract_pdf_text(
            file_path,
        )

    if content_type in {
        "image/png",
        "image/jpeg",
        "image/jpg",
    }:
        return extract_image_text(
            file_path,
        )

    raise ValueError(
        f"Unsupported document type: {content_type}"
    )


# ==========================================================
# AUTOMATIC CLASSIFICATION
# ==========================================================

async def classify_processed_document(
    extracted_text: str,
) -> str:
    """
    Call the existing Ollama classifier directly.

    This avoids an HTTP request from the backend to its own
    /document-classification endpoint and avoids circular imports.
    """
    from app.modules.document_classifier import (
        classify_with_ollama,
    )

    document_type = await classify_with_ollama(
        extracted_text,
    )

    if not document_type:
        raise ValueError(
            "Document classifier returned no document type."
        )

    return str(
        document_type
    ).upper().strip()


# ==========================================================
# PROCESS ONE DOCUMENT
# ==========================================================

async def process_document_record(
    document_id: uuid.UUID,
) -> bool:
    """
    Complete extraction + classification using a fresh DB session.

    This function is safe for FastAPI BackgroundTasks.
    """

    async with AsyncSessionLocal() as db:

        document = await db.get(
            PatientDocument,
            document_id,
        )

        if (
            document is None
            or document.deleted_at is not None
        ):
            logger.warning(
                "AGCT pipeline: document %s not found.",
                document_id,
            )
            return False

        current_status = str(
            document.processing_status or ""
        ).upper()

        # Already complete is only truly complete when a classification
        # exists. Older broken rows may be COMPLETED with NULL type.
        if (
            current_status == "COMPLETED"
            and document.document_type
            and document.extracted_text
        ):
            logger.info(
                "AGCT pipeline: document %s already complete.",
                document_id,
            )
            return True

        if current_status == "PROCESSING":
            logger.info(
                "AGCT pipeline: document %s already processing.",
                document_id,
            )
            return False

        patient = await db.get(
            Patient,
            document.patient_id,
        )

        if (
            patient is None
            or patient.deleted_at is not None
        ):
            logger.error(
                "AGCT pipeline: patient missing for document %s.",
                document_id,
            )

            document.processing_status = "FAILED"
            await db.commit()
            return False

        try:
            # --------------------------------------------------
            # STAGE 1 — PROCESSING
            # --------------------------------------------------

            document.processing_status = "PROCESSING"
            await db.commit()

            logger.info(
                "AGCT pipeline: PROCESSING %s | %s",
                document_id,
                document.original_filename,
            )

            # --------------------------------------------------
            # STAGE 2 — TEXT EXTRACTION
            # --------------------------------------------------

            extracted_text = extract_document_text(
                document,
            )

            if not extracted_text.strip():
                raise ValueError(
                    "No text could be extracted from the document."
                )

            document.extracted_text = (
                extracted_text.strip()
            )

            await db.commit()

            logger.info(
                "AGCT pipeline: extracted %d chars | %s",
                len(document.extracted_text),
                document.original_filename,
            )

            # --------------------------------------------------
            # STAGE 3 — CLASSIFICATION
            # --------------------------------------------------

            logger.info(
                "AGCT pipeline: CLASSIFYING %s",
                document.original_filename,
            )

            document_type = (
                await classify_processed_document(
                    document.extracted_text,
                )
            )

            document.document_type = document_type

            await db.commit()

            logger.info(
                "AGCT pipeline: CLASSIFIED %s -> %s",
                document.original_filename,
                document.document_type,
            )

            # --------------------------------------------------
            # STAGE 4 — COMPLETED
            # --------------------------------------------------

            document.processing_status = "COMPLETED"

            await db.commit()
            await db.refresh(
                document,
            )

            logger.info(
                "AGCT pipeline: COMPLETE | %s | type=%s",
                document.original_filename,
                document.document_type,
            )

            return True

        except Exception as exc:
            logger.exception(
                "AGCT pipeline failed for %s: %s",
                document_id,
                exc,
            )

            await db.rollback()

            failed_document = await db.get(
                PatientDocument,
                document_id,
            )

            if (
                failed_document is not None
                and failed_document.deleted_at is None
            ):
                failed_document.processing_status = "FAILED"
                await db.commit()

            return False


# ==========================================================
# BACKGROUND ENTRY POINT
# ==========================================================

async def process_document_background(
    document_id: uuid.UUID,
) -> None:
    """
    Called automatically after upload commit.
    """
    logger.info(
        "AGCT automatic pipeline STARTED | %s",
        document_id,
    )

    try:
        await process_document_record(
            document_id,
        )
    except Exception:
        logger.exception(
            "AGCT automatic pipeline crashed | %s",
            document_id,
        )


# ==========================================================
# MANUAL PROCESS ENDPOINT
# ==========================================================

@router.post(
    "/{document_id}/process",
)
async def process_document(
    document_id: uuid.UUID,
    current_user: User = Depends(
        DoctorOnly,
    ),
    db: AsyncSession = Depends(
        get_db,
    ),
):
    """
    Backward-compatible endpoint.

    The frontend no longer needs to call this after upload.
    If an automatic worker is already running, wait for it instead
    of creating a second worker.
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

    patient = await db.get(
        Patient,
        document.patient_id,
    )

    if (
        patient is None
        or patient.deleted_at is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    if (
        str(document.processing_status or "").upper()
        == "PROCESSING"
    ):
        waited = 0
        max_wait = 300

        while waited < max_wait:
            await asyncio.sleep(1)
            waited += 1

            await db.refresh(
                document,
            )

            current = str(
                document.processing_status or ""
            ).upper()

            if current in {
                "COMPLETED",
                "FAILED",
            }:
                break

        if str(
            document.processing_status or ""
        ).upper() == "PROCESSING":
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=(
                    "Automatic document processing is still running."
                ),
            )

        if str(
            document.processing_status or ""
        ).upper() == "FAILED":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Automatic document processing failed. "
                    "Check the backend terminal."
                ),
            )

        return {
            "message": (
                "Document was processed and classified "
                "by the automatic pipeline."
            ),
            "document_id": str(
                document.id
            ),
            "patient_id": str(
                document.patient_id
            ),
            "filename": document.original_filename,
            "processing_status": document.processing_status,
            "document_type": document.document_type,
            "extracted_text_length": len(
                document.extracted_text or ""
            ),
        }

    success = await process_document_record(
        document_id,
    )

    await db.refresh(
        document,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Document pipeline failed. "
                "Check the backend terminal."
            ),
        )

    return {
        "message": (
            "Document processed and classified successfully."
        ),
        "document_id": str(
            document.id
        ),
        "patient_id": str(
            document.patient_id
        ),
        "filename": document.original_filename,
        "processing_status": document.processing_status,
        "document_type": document.document_type,
        "extracted_text_length": len(
            document.extracted_text or ""
        ),
    }


# ==========================================================
# RECOVERY ENDPOINT
# ==========================================================

@router.post(
    "/process-pending",
)
async def process_pending_documents(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(
        DoctorOnly,
    ),
    db: AsyncSession = Depends(
        get_db,
    ),
):
    """
    Recover documents left behind by an older pipeline.

    Includes:
      - PENDING
      - FAILED
      - COMPLETED + extracted text + missing document_type
    """

    result = await db.scalars(
        select(
            PatientDocument,
        )
        .where(
            PatientDocument.deleted_at.is_(None),
            or_(
                PatientDocument.processing_status == "PENDING",
                PatientDocument.processing_status == "FAILED",
                (
                    PatientDocument.processing_status == "COMPLETED"
                )
                & PatientDocument.document_type.is_(None),
            ),
        )
        .order_by(
            PatientDocument.created_at.asc(),
        )
    )

    documents = result.all()

    for document in documents:
        background_tasks.add_task(
            process_document_background,
            document.id,
        )

    return {
        "message": (
            "Recovery pipeline queued pending, failed, "
            "and unclassified documents."
        ),
        "queued": len(
            documents
        ),
        "documents": [
            {
                "document_id": str(
                    document.id
                ),
                "filename": (
                    document.original_filename
                ),
                "processing_status": (
                    document.processing_status
                ),
                "document_type": (
                    document.document_type
                ),
            }
            for document in documents
        ],
    }