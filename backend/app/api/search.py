"""
Top-level semantic search endpoint.

  POST /search

Accepts a free-text query and returns the top-k most relevant document chunks
from the specified workspace, shaped for the eval runner and the frontend chat
UI. This is a thin wrapper around vector_store.query() that:

  1. Runs ChromaDB similarity search scoped to the workspace
  2. Enriches each result with the source document filename
  3. Returns a stable response envelope: {"results": [...]}

The `source` field in each result maps directly to `expected_source_doc` in
eval_questions.csv, which is how the eval runner calculates top-3 recall.

Note: for production use the workspace_id should be derived from the
authenticated user's session. It is in the request body here so the eval
runner and Swagger UI can target any workspace without authentication.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.services import vector_store

router = APIRouter(tags=["search"])


# ── request / response models ──────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Free-text question or keyword query")
    workspace_id: int = Field(..., description="Workspace to search within")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")


class SearchResult(BaseModel):
    source: str          = Field(..., description="Filename of the source document")
    content: str         = Field(..., description="Raw text of the matching chunk")
    document_id: int     = Field(..., description="PK of the Document row")
    chunk_index: int     = Field(..., description="Zero-based position within the document")
    distance: float      = Field(..., description="Cosine distance — lower means more relevant")


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str
    workspace_id: int


# ── endpoint ───────────────────────────────────────────────────────────────────

@router.post("/search", response_model=SearchResponse)
def search(body: SearchRequest, db: Session = Depends(get_db)):
    """
    Semantic search across all indexed document chunks in a workspace.

    Returns up to `top_k` chunks ranked by cosine similarity to the query.
    Only chunks that have been embedded (via POST /…/chunk) will appear.

    The `source` field in each result contains the document filename —
    this is the value compared against `expected_source_doc` in the eval CSV.
    """
    raw_results = vector_store.query(
        body.query,
        workspace_id=body.workspace_id,
        n_results=body.top_k,
    )

    # Enrich with filenames in a single pass, caching per document_id to avoid
    # N+1 queries when multiple chunks come from the same document.
    doc_cache: dict[int, Document | None] = {}
    results: list[SearchResult] = []

    for r in raw_results:
        doc_id = r["document_id"]
        if doc_id not in doc_cache:
            doc_cache[doc_id] = db.query(Document).filter(Document.id == doc_id).first()
        doc = doc_cache[doc_id]

        results.append(
            SearchResult(
                source=doc.filename if doc else "unknown",
                content=r["content"],
                document_id=doc_id,
                chunk_index=r["chunk_index"],
                distance=r["distance"],
            )
        )

    return SearchResponse(
        results=results,
        query=body.query,
        workspace_id=body.workspace_id,
    )
