"""
Documents API — upload, list, and text extraction endpoints.

Upload is intentionally fast: it saves the file and returns immediately
with status=pending. Text extraction is a separate step triggered explicitly
by the frontend, either for a single document or a batch.

  POST   /workspaces/{id}/documents/upload            → save file, status=pending
  GET    /workspaces/{id}/documents/                  → list docs (no content)
  POST   /workspaces/{id}/documents/{doc_id}/process  → extract text (single)
  POST   /workspaces/{id}/documents/process-batch     → extract text (many)

All routes are scoped under /workspaces/{workspace_id}/documents so documents
always belong to a workspace (matching the data model).
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document, ProcessingStatus
from app.services import ingestion, storage

router = APIRouter(
    prefix="/workspaces/{workspace_id}/documents",
    tags=["documents"],
)


# ── helpers ────────────────────────────────────────────────────────────────────

def _run_extraction(doc: Document, db: Session) -> None:
    """
    Extract text from a single Document and update its DB row in place.
    Shared by both the single-doc and batch endpoints to avoid duplication.
    """
    if not doc.storage_path:
        doc.processing_status = ProcessingStatus.failed
        doc.processing_error = "No file on disk to process."
        return

    abs_path = Path(__file__).parent.parent.parent / doc.storage_path
    doc.processing_status = ProcessingStatus.processing
    db.commit()

    try:
        doc.content = ingestion.extract_text(abs_path, doc.file_type)
        doc.processing_status = ProcessingStatus.complete
        doc.processing_error = None
    except Exception as exc:
        doc.processing_status = ProcessingStatus.failed
        doc.processing_error = str(exc)

    db.commit()
    db.refresh(doc)


# ── endpoints ──────────────────────────────────────────────────────────────────

@router.post("/upload", status_code=201)
def upload_document(
    workspace_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    """
    Save an uploaded file to disk and create a Document row (status=pending).
    Returns immediately — text extraction is NOT triggered here.
    Call /process or /process-batch when you're ready to extract text.
    """
    try:
        file_type = ingestion.get_file_type(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    abs_path, file_size = storage.save_upload(file, workspace_id)
    relative_path = str(abs_path.relative_to(Path(__file__).parent.parent.parent))

    doc = Document(
        workspace_id=workspace_id,
        filename=file.filename,
        file_type=file_type,
        file_size=file_size,
        storage_path=relative_path,
        processing_status=ProcessingStatus.pending,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "processing_status": doc.processing_status,
    }


@router.get("/")
def list_documents(workspace_id: int, db: Session = Depends(get_db)):
    """Return all documents in a workspace, without their full text content."""
    docs = db.query(Document).filter(Document.workspace_id == workspace_id).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "file_size": d.file_size,
            "processing_status": d.processing_status,
            "created_at": d.created_at,
        }
        for d in docs
    ]


@router.post("/{doc_id}/process")
def process_document(
    workspace_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
):
    """
    Trigger text extraction for a single document.
    The document must belong to the given workspace.
    Can be called again to re-process a failed document.
    """
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.workspace_id == workspace_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    _run_extraction(doc, db)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "processing_status": doc.processing_status,
        "processing_error": doc.processing_error,
        "content_length": len(doc.content) if doc.content else 0,
    }


class BatchProcessRequest(BaseModel):
    """Request body for the batch process endpoint."""
    document_ids: list[int]


@router.post("/process-batch")
def process_batch(
    workspace_id: int,
    body: BatchProcessRequest,
    db: Session = Depends(get_db),
):
    """
    Trigger text extraction for a list of document IDs.
    Only processes documents that belong to this workspace.
    Returns a summary of how many succeeded, failed, or were not found.
    """
    results = {"complete": [], "failed": [], "not_found": []}

    for doc_id in body.document_ids:
        doc = (
            db.query(Document)
            .filter(Document.id == doc_id, Document.workspace_id == workspace_id)
            .first()
        )
        if not doc:
            results["not_found"].append(doc_id)
            continue

        _run_extraction(doc, db)

        if doc.processing_status == ProcessingStatus.complete:
            results["complete"].append(doc_id)
        else:
            results["failed"].append({"id": doc_id, "error": doc.processing_error})

    return results
