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
from app.models.document import Document, DocumentChunk, ProcessingStatus
from app.services import chunking, ingestion, storage, vector_store

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


@router.get("/search")
def search_documents(
    workspace_id: int,
    q: str,
    n: int = 5,
    db: Session = Depends(get_db),
):
    """
    Semantic search across all indexed chunks in a workspace.
    Returns the n most relevant chunks for the query string, enriched with
    the source document filename.

    Requires documents to have been chunked (POST /{doc_id}/chunk) — only
    chunks that have been embedded and stored in ChromaDB will appear here.
    """
    results = vector_store.query(q, workspace_id=workspace_id, n_results=n)

    # Enrich each result with the source document filename so the frontend
    # can display "from Deposition_Smith.pdf" without a second request.
    doc_cache: dict[int, Document] = {}
    for result in results:
        doc_id = result["document_id"]
        if doc_id not in doc_cache:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            doc_cache[doc_id] = doc
        doc = doc_cache[doc_id]
        result["filename"] = doc.filename if doc else None

    return results


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


@router.post("/{doc_id}/chunk")
def chunk_document(
    workspace_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
):
    """
    Split a document's extracted text into chunks and store them in the
    document_chunks table. Requires the document to already be processed
    (status=complete). Replaces any existing chunks so it is safe to call
    multiple times.

    This is the step that prepares documents for the RAG pipeline —
    each chunk will later get an embedding and be stored in ChromaDB.
    """
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.workspace_id == workspace_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.processing_status != ProcessingStatus.complete:
        raise HTTPException(
            status_code=422,
            detail=f"Document must be processed before chunking (current status: {doc.processing_status}).",
        )
    if not doc.content:
        raise HTTPException(status_code=422, detail="Document has no extracted text to chunk.")

    # Purge existing Postgres rows and ChromaDB vectors so re-chunking is safe.
    # ChromaDB delete must happen before the DB delete — both use doc_id.
    vector_store.delete_document_chunks(doc_id)
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()

    chunks = chunking.split_text(doc.content)

    # Build ORM objects first so we can attach embedding_ids after the upsert.
    db_chunks = []
    for chunk in chunks:
        db_chunk = DocumentChunk(
            document_id=doc_id,
            chunk_index=chunk.index,
            content=chunk.content,
            token_count=chunk.token_count,
        )
        db.add(db_chunk)
        db_chunks.append(db_chunk)

    # Embed and store in ChromaDB. Returns deterministic IDs — no DB flush needed.
    embedding_ids = vector_store.upsert_chunks(doc_id, doc.workspace_id, chunks)

    for db_chunk, emb_id in zip(db_chunks, embedding_ids):
        db_chunk.embedding_id = emb_id

    db.commit()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "chunk_count": len(chunks),
        "total_tokens": sum(c.token_count for c in chunks),
    }
