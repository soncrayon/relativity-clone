"""
ChromaDB vector store wrapper for document chunk embeddings.

Think of this as a specialized search index that understands *meaning*, not just
keywords. When a chunk is stored here, it is first converted to a vector — a list
of ~384 numbers that encode the semantic content of the text. When a user searches,
their query is converted the same way, and ChromaDB returns the chunks whose vectors
are closest (i.e. most semantically similar).

Two public operations:
  upsert_chunks(doc_id, workspace_id, chunks) — embed and store chunks
  query(text, workspace_id, n_results)        — find similar chunks
  delete_document_chunks(doc_id)              — remove all vectors for a document

Call init() once at FastAPI startup to load the embedding model and connect to
ChromaDB. Subsequent calls are fast — the model stays in memory.
"""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

# ── constants ──────────────────────────────────────────────────────────────────

# Local model that runs fully offline — no API key, no cost, ~80 MB download on
# first use (cached in ~/.cache/huggingface/ after that). Produces 384-dim vectors.
MODEL_NAME = "all-MiniLM-L6-v2"

COLLECTION_NAME = "document_chunks"

# Persistent ChromaDB storage alongside the document file storage
CHROMA_PATH = Path(__file__).parent.parent.parent / "storage" / "chroma"

# ── module-level state (initialized once at startup) ──────────────────────────

_collection: chromadb.Collection | None = None
_model: SentenceTransformer | None = None


# ── lifecycle ──────────────────────────────────────────────────────────────────

def init() -> None:
    """
    Load the embedding model and connect to ChromaDB.

    Called once in the FastAPI lifespan so the first request doesn't pay the
    model-load cost (~5–10 s on first run while the model downloads).
    Subsequent server starts are fast because the model is cached locally.
    """
    global _collection, _model

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)

    print(f"Loading embedding model '{MODEL_NAME}'…")
    _model = SentenceTransformer(MODEL_NAME)

    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    _collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        # Cosine similarity is standard for text — measures the angle between
        # vectors rather than raw distance, so chunk length doesn't skew results.
        metadata={"hnsw:space": "cosine"},
    )
    print(f"ChromaDB ready — {_collection.count()} chunks indexed")


def _require_init() -> None:
    """Raise a clear error if init() was not called before using the store."""
    if _collection is None or _model is None:
        raise RuntimeError(
            "vector_store.init() must be called before using the store. "
            "This should happen automatically in the FastAPI lifespan."
        )


# ── public API ─────────────────────────────────────────────────────────────────

def upsert_chunks(doc_id: int, workspace_id: int, chunks: list) -> list[str]:
    """
    Embed a list of Chunk objects (from services/chunking.py) and upsert them
    into ChromaDB.

    Uses upsert (not add) so re-chunking a document is safe — existing vectors
    are overwritten rather than duplicated. Call delete_document_chunks() first
    if the chunk count may decrease (otherwise stale vectors from prior runs linger).

    Each entry in ChromaDB stores:
      id        — deterministic string: "doc_{doc_id}_chunk_{chunk.index}"
      embedding — 384-dim float vector produced by all-MiniLM-L6-v2
      document  — the raw chunk text (so search results are self-contained)
      metadata  — document_id, workspace_id, chunk_index (used for RBAC filtering)

    Returns the list of ChromaDB IDs in the same order as input chunks.
    """
    _require_init()

    if not chunks:
        return []

    ids = [f"doc_{doc_id}_chunk_{c.index}" for c in chunks]
    texts = [c.content for c in chunks]
    metadatas = [
        {
            "document_id": doc_id,
            "workspace_id": workspace_id,
            "chunk_index": c.index,
        }
        for c in chunks
    ]

    # encode() returns a numpy array by default, which chromadb 0.4.x accepts directly.
    embeddings = _model.encode(texts)

    _collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return ids


def delete_document_chunks(doc_id: int) -> None:
    """
    Remove all ChromaDB entries for a given document.
    Call this before re-chunking so stale vectors from the previous run are purged.
    Safe to call if the document has no vectors (no-op).
    """
    _require_init()
    _collection.delete(where={"document_id": doc_id})


def query(text: str, workspace_id: int, n_results: int = 5) -> list[dict]:
    """
    Return the n_results most semantically similar chunks to `text` within
    the given workspace.

    The workspace_id filter is what makes search RBAC-aware in Phase 3 —
    a user can only retrieve chunks from workspaces they have access to.

    Each result dict contains:
      id           — ChromaDB entry ID (e.g. "doc_3_chunk_12")
      content      — the raw chunk text
      document_id  — FK to documents table
      chunk_index  — position of this chunk within the document
      distance     — cosine distance (0 = identical, 2 = opposite; lower = more relevant)
    """
    _require_init()

    if _collection.count() == 0:
        return []

    embedding = _model.encode([text])

    try:
        results = _collection.query(
            query_embeddings=embedding,
            n_results=n_results,
            where={"workspace_id": workspace_id},
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        # ChromaDB raises if n_results exceeds the number of indexed items.
        # Fall back to fetching whatever is available.
        count = _collection.count()
        if count == 0:
            return []
        results = _collection.query(
            query_embeddings=embedding,
            n_results=count,
            where={"workspace_id": workspace_id},
            include=["documents", "metadatas", "distances"],
        )

    # ChromaDB returns nested lists (supports multi-query); we always send one query.
    out = []
    for i, entry_id in enumerate(results["ids"][0]):
        out.append(
            {
                "id": entry_id,
                "content": results["documents"][0][i],
                "document_id": results["metadatas"][0][i]["document_id"],
                "chunk_index": results["metadatas"][0][i]["chunk_index"],
                "distance": results["distances"][0][i],
            }
        )
    return out
