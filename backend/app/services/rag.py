"""
RAG (Retrieval-Augmented Generation) query pipeline.

This is the core of Phase 2 — the service that turns a user's question into
a cited answer by combining ChromaDB vector search with an LLM.

The pipeline in order:
  1. Query ChromaDB for the top-k semantically similar chunks (workspace-scoped)
  2. Pass the chunk texts as context to the configured LLM provider
  3. Map the LLM's [1], [2] citation markers back to real DocumentChunk DB rows
  4. Validate citations — drop any that don't map to a real chunk (anti-hallucination)
  5. Return a RagResponse with the answer, validated citations, and confidence

The workspace_id scoping in step 1 is what makes retrieval RBAC-aware in
Phase 3 — the model literally cannot see chunks from workspaces the user
can't access, because they're never retrieved.

Usage:
    from app.services.rag import ask
    from sqlalchemy.orm import Session

    response = ask(
        question="What did the defendant say about the wire transfers?",
        workspace_id=3,
        db=db,
    )
    print(response.answer)
    for c in response.citations:
        print(c.document_filename, "chunk", c.chunk_index)
"""

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.services import vector_store
from app.services.llm import get_provider

# How many chunks to retrieve from ChromaDB per query.
# 5 is a good default — enough context without overwhelming the LLM's context
# window or introducing irrelevant passages that confuse the answer.
TOP_K = 5


# ── response types ─────────────────────────────────────────────────────────────

@dataclass
class ValidatedCitation:
    """
    A citation that has been confirmed to reference a real DocumentChunk.

    After the LLM emits "[1]", "[2]" etc., we resolve each marker back to
    the actual chunk it refers to and verify it exists in PostgreSQL.
    Any marker the model invented (pointing to a non-existent chunk) is
    silently dropped — this is the anti-hallucination guard.
    """
    marker: str             # "[1]", "[2]", etc. — matches the text in the answer
    chunk_id: str           # ChromaDB entry ID, e.g. "doc_3_chunk_12"
    document_id: int        # FK to documents table
    document_filename: str  # e.g. "Deposition_Smith_2024.pdf"
    chunk_index: int        # 0-based position within the document
    text_snippet: str       # First 200 chars of the chunk — shown in the UI tooltip
    page_number: int | None # Page the chunk starts on, if known


@dataclass
class RagResponse:
    """
    The final output of the RAG pipeline, ready to be serialised by the API.

    answer           — the LLM's response text, with [1], [2] markers inline
    citations        — validated citations only (hallucinated ones are excluded)
    confidence       — 0.0–1.0 score from the LLM provider
    chunks_retrieved — how many chunks were sent to the LLM as context
    no_context       — True if ChromaDB had no indexed chunks for this workspace
    """
    answer: str
    citations: list[ValidatedCitation] = field(default_factory=list)
    confidence: float = 0.8
    chunks_retrieved: int = 0
    no_context: bool = False


# ── public API ─────────────────────────────────────────────────────────────────

def ask(question: str, workspace_id: int, db: Session) -> RagResponse:
    """
    Run the full RAG pipeline for a single question.

    Parameters
    ----------
    question     : The user's natural-language question.
    workspace_id : Scopes retrieval to only chunks from this workspace.
    db           : SQLAlchemy session used to validate citations and fetch metadata.

    Returns
    -------
    RagResponse with answer text, validated citations, and metadata.
    """
    # ── Step 1: Retrieve relevant chunks from ChromaDB ─────────────────────────
    search_results = vector_store.query(question, workspace_id=workspace_id, n_results=TOP_K)

    if not search_results:
        return RagResponse(
            answer=(
                "I couldn't find any relevant documents to answer your question. "
                "Make sure documents have been uploaded, processed, and chunked in "
                "this workspace before asking questions."
            ),
            no_context=True,
        )

    # ── Step 2: Build context list and chunk ID index ──────────────────────────
    # context_texts is what the LLM sees — ordered list of chunk texts.
    # chunk_ids maps position (1-indexed, matching [1] [2] in the answer)
    # back to the ChromaDB entry ID for citation resolution below.
    context_texts: list[str] = [r["content"] for r in search_results]
    chunk_ids: list[str] = [r["id"] for r in search_results]  # e.g. "doc_3_chunk_12"

    # ── Step 3: Call the LLM ───────────────────────────────────────────────────
    provider = get_provider()
    llm_response = provider.generate(prompt=question, context=context_texts)

    # ── Step 4: Validate citations (anti-hallucination guard) ──────────────────
    validated = _validate_citations(llm_response.citations, chunk_ids, db)

    return RagResponse(
        answer=llm_response.answer,
        citations=validated,
        confidence=llm_response.confidence,
        chunks_retrieved=len(search_results),
    )


# ── private helpers ────────────────────────────────────────────────────────────

def _validate_citations(
    raw_citations: list,
    chunk_ids: list[str],
    db: Session,
) -> list[ValidatedCitation]:
    """
    Resolve LLM citation markers to real DocumentChunk DB rows.

    The LLM provider emits Citation objects where chunk_id is a 1-based
    position string (e.g. "1" meaning the first context chunk). This
    function:
      1. Converts the position to the actual ChromaDB entry ID
      2. Looks up the DocumentChunk in PostgreSQL via embedding_id
      3. If found, builds a ValidatedCitation with full metadata
      4. If not found (hallucinated reference), silently skips it

    Returns only citations that point to real, existing chunks.
    """
    validated: list[ValidatedCitation] = []
    seen_chunk_ids: set[str] = set()

    for citation in raw_citations:
        # citation.chunk_id is the 1-based position string from the parser
        try:
            position = int(citation.chunk_id)
        except ValueError:
            continue  # malformed marker — skip

        # Convert 1-based position to 0-based index into chunk_ids list
        idx = position - 1
        if idx < 0 or idx >= len(chunk_ids):
            continue  # citation number out of range — skip

        chroma_id = chunk_ids[idx]

        # Deduplicate: the model sometimes cites the same source twice
        if chroma_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(chroma_id)

        # Look up the chunk in PostgreSQL using the embedding_id FK
        chunk = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.embedding_id == chroma_id)
            .first()
        )
        if chunk is None:
            # ChromaDB has the vector but the DB row is gone (stale index).
            # Skip rather than returning a broken citation.
            continue

        # Fetch the parent document for filename metadata
        doc = db.query(Document).filter(Document.id == chunk.document_id).first()
        if doc is None:
            continue

        validated.append(
            ValidatedCitation(
                marker=citation.marker,
                chunk_id=chroma_id,
                document_id=chunk.document_id,
                document_filename=doc.filename,
                chunk_index=chunk.chunk_index,
                text_snippet=chunk.content[:200],
                page_number=chunk.page_number,
            )
        )

    return validated
