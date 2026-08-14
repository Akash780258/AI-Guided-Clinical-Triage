"""
AGCT Patient File Upload

Handles patient-specific medical document uploads.

The system stores:

1. The physical file on disk.
2. A PatientDocument database record.

Every document is explicitly associated with a patient_id.

Supported:
- PDF
- PNG
- JPG
- JPEG

Maximum file size:
- 10 MB

Processing pipeline:

    UPLOAD
       ↓
    PENDING
       ↓
    BACKGROUND PROCESSOR
       ↓
    PROCESSING
       ↓
    TEXT EXTRACTION
       ↓
    DOCUMENT CLASSIFICATION
       ↓
    COMPLETED

If extraction or classification fails:

    PROCESSING
       ↓
    FAILED
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DoctorOnly
from app.database.session import get_db

from app.modules.auth.models import User

from app.modules.document_processor import (
    process_document_background,
)

from app.modules.patients.documents import (
    PatientDocument,
)

from app.modules.patients.models import (
    Patient,
)


# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_UPLOAD_DIR = (
    Path("uploads") / "patients"
)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
}

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}

MAX_FILE_SIZE = (
    10 * 1024 * 1024
)


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/patients",
    tags=["Patient Files"],
)


# ==========================================================
# HELPERS
# ==========================================================

def get_file_extension(
    filename: str,
) -> str:
    """
    Return a normalized file extension.
    """

    return Path(
        filename
    ).suffix.lower()


def validate_file_type(
    file: UploadFile,
) -> str:
    """
    Validate uploaded file extension and MIME type.
    """

    if not file.filename:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A file name is required.",
        )

    extension = get_file_extension(
        file.filename
    )

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported file type. "
                "Allowed types: PDF, PNG, JPG, JPEG."
            ),
        )

    if (
        file.content_type
        not in ALLOWED_CONTENT_TYPES
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file content type.",
        )

    return extension


# ==========================================================
# UPLOAD PATIENT FILE
# ==========================================================

@router.post(
    "/{patient_id}/files",
    status_code=status.HTTP_201_CREATED,
)
async def upload_patient_file(
    patient_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(
        DoctorOnly,
    ),
    db: AsyncSession = Depends(
        get_db,
    ),
):
    """
    Upload a medical document for a specific patient.

    The database record is created first.

    Only after the database transaction succeeds do we
    queue the background processing task.

    Background processing performs:

        extraction
        ↓
        classification
        ↓
        COMPLETED

    The upload request itself does not wait for Ollama.
    """

    # ======================================================
    # 1. VALIDATE PATIENT
    # ======================================================

    patient = await db.get(
        Patient,
        patient_id,
    )

    if (
        patient is None
        or patient.deleted_at is not None
    ):

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    # ======================================================
    # 2. VALIDATE FILE
    # ======================================================

    extension = validate_file_type(
        file
    )

    # ======================================================
    # 3. CREATE PATIENT DIRECTORY
    # ======================================================

    patient_directory = (
        BASE_UPLOAD_DIR
        / str(patient_id)
    )

    patient_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ======================================================
    # 4. GENERATE SAFE STORAGE FILENAME
    # ======================================================

    stored_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    stored_path = (
        patient_directory
        / stored_filename
    )

    # ======================================================
    # 5. SAVE PHYSICAL FILE
    # ======================================================

    total_size = 0

    try:

        with stored_path.open(
            "wb"
        ) as destination:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                total_size += len(
                    chunk
                )

                # ------------------------------------------
                # MAXIMUM FILE SIZE
                # ------------------------------------------

                if (
                    total_size
                    > MAX_FILE_SIZE
                ):

                    if stored_path.exists():
                        stored_path.unlink()

                    raise HTTPException(
                        status_code=(
                            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                        ),
                        detail=(
                            "File size cannot exceed 10 MB."
                        ),
                    )

                destination.write(
                    chunk
                )

    except HTTPException:
        raise

    except Exception as exc:

        if stored_path.exists():
            stored_path.unlink()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Failed to save uploaded file."
            ),
        ) from exc

    finally:

        await file.close()

    # ======================================================
    # 6. CREATE DATABASE DOCUMENT
    # ======================================================

    document = PatientDocument(
        patient_id=patient_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=str(
            stored_path
        ),
        content_type=(
            file.content_type
            or "application/octet-stream"
        ),
        file_size=total_size,

        # ------------------------------------------
        # IMPORTANT:
        # Classification has NOT happened yet.
        # ------------------------------------------

        document_type=None,

        description=None,

        # ------------------------------------------
        # Initial state.
        # Background processor will change this to:
        #
        # PROCESSING
        # COMPLETED
        #
        # or:
        #
        # FAILED
        # ------------------------------------------

        processing_status="PENDING",

        extracted_text=None,

        uploaded_by_id=current_user.id,
    )

    # ======================================================
    # 7. SAVE DATABASE RECORD
    # ======================================================

    try:

        db.add(
            document
        )

        await db.commit()

        await db.refresh(
            document
        )

    except Exception as exc:

        await db.rollback()

        # --------------------------------------------------
        # Database failed.
        # Remove physical file.
        # --------------------------------------------------

        if stored_path.exists():
            stored_path.unlink()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "File was not registered "
                "in the database."
            ),
        ) from exc

    # ======================================================
    # 8. QUEUE BACKGROUND PROCESSING
    # ======================================================

    """
    IMPORTANT:

    Do this AFTER db.commit().

    The background processor receives only the document ID
    and opens its own database session.

    It will perform:

        PENDING
          ↓
        PROCESSING
          ↓
        extract_document_text()
          ↓
        document.extracted_text
          ↓
        classify_document_record()
          ↓
        document.document_type
          ↓
        COMPLETED
    """

    background_tasks.add_task(
        process_document_background,
        document.id,
    )

    # ======================================================
    # 9. RESPONSE
    # ======================================================

    return {
        "message": (
            "File uploaded successfully "
            "and queued for processing."
        ),

        "document_id": str(
            document.id
        ),

        "patient_id": str(
            document.patient_id
        ),

        "filename": (
            document.original_filename
        ),

        "stored_filename": (
            document.stored_filename
        ),

        "content_type": (
            document.content_type
        ),

        "size": (
            document.file_size
        ),

        "path": (
            document.file_path
        ),

        # This will initially be None.
        # The background processor will populate it.
        "document_type": (
            document.document_type
        ),

        # This will initially be PENDING.
        # The background processor will update it.
        "processing_status": (
            document.processing_status
        ),

        "uploaded_by": str(
            document.uploaded_by_id
        ),

        "created_at": (
            document.created_at
        ),
    }


# ==========================================================
# LIST PATIENT DOCUMENTS
# ==========================================================

@router.get(
    "/{patient_id}/files",
)
async def list_patient_files(
    patient_id: uuid.UUID,
    current_user: User = Depends(
        DoctorOnly,
    ),
    db: AsyncSession = Depends(
        get_db,
    ),
):
    """
    Return all active documents belonging to a patient.

    The database is the source of truth.
    """

    # ======================================================
    # VALIDATE PATIENT
    # ======================================================

    patient = await db.get(
        Patient,
        patient_id,
    )

    if (
        patient is None
        or patient.deleted_at is not None
    ):

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    # ======================================================
    # QUERY DOCUMENTS
    # ======================================================

    result = await db.scalars(
        select(
            PatientDocument
        )
        .where(
            PatientDocument.patient_id
            == patient_id,

            PatientDocument.deleted_at.is_(None),
        )
        .order_by(
            PatientDocument.created_at.desc()
        )
    )

    documents = result.all()

    # ======================================================
    # RESPONSE
    # ======================================================

    return {
        "patient_id": str(
            patient_id
        ),

        "total": len(
            documents
        ),

        "files": [
            {
                "document_id": str(
                    document.id
                ),

                "filename": (
                    document.original_filename
                ),

                "stored_filename": (
                    document.stored_filename
                ),

                "content_type": (
                    document.content_type
                ),

                "size": (
                    document.file_size
                ),

                "document_type": (
                    document.document_type
                ),

                "description": (
                    document.description
                ),

                "processing_status": (
                    document.processing_status
                ),

                "path": (
                    document.file_path
                ),

                "uploaded_by": str(
                    document.uploaded_by_id
                ),

                "created_at": (
                    document.created_at
                ),

                "updated_at": (
                    document.updated_at
                ),
            }

            for document in documents
        ],
    }


# ==========================================================
# DOWNLOAD PATIENT DOCUMENT
# ==========================================================

@router.get(
    "/{patient_id}/files/{filename}",
)
async def download_patient_file(
    patient_id: uuid.UUID,
    filename: str,
    current_user: User = Depends(
        DoctorOnly,
    ),
    db: AsyncSession = Depends(
        get_db,
    ),
):
    """
    Download a document belonging to a patient.
    """

    # ======================================================
    # VALIDATE PATIENT
    # ======================================================

    patient = await db.get(
        Patient,
        patient_id,
    )

    if (
        patient is None
        or patient.deleted_at is not None
    ):

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    # ======================================================
    # PREVENT PATH TRAVERSAL
    # ======================================================

    safe_filename = Path(
        filename
    ).name

    # ======================================================
    # FIND DATABASE DOCUMENT
    # ======================================================

    document = await db.scalar(
        select(
            PatientDocument
        )
        .where(
            PatientDocument.patient_id
            == patient_id,

            PatientDocument.stored_filename
            == safe_filename,

            PatientDocument.deleted_at.is_(None),
        )
    )

    if document is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )

    # ======================================================
    # VERIFY PHYSICAL FILE
    # ======================================================

    file_path = Path(
        document.file_path
    )

    if (
        not file_path.exists()
        or not file_path.is_file()
    ):

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "The document exists in the database, "
                "but the physical file is missing."
            ),
        )

    # ======================================================
    # RETURN FILE
    # ======================================================

    return FileResponse(
        path=file_path,
        filename=document.original_filename,
        media_type=document.content_type,
    )