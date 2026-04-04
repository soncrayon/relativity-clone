import enum
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ProcessingStatus(str, enum.Enum):
    pending = "pending"      # Uploaded but not yet processed
    processing = "processing"  # Text extraction in progress
    complete = "complete"    # Text extracted and chunks stored
    failed = "failed"        # Processing encountered an error


class Document(Base):
    """
    Represents an uploaded legal document. The raw file is stored on disk;
    this table stores the extracted text and metadata needed for search and RAG.
    """

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # The original filename shown to users (e.g. "Deposition_Smith_2024.pdf")
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    # Normalized file extension: "pdf", "docx", "txt", "eml"
    file_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # File size in bytes — useful for displaying in the UI
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Path to the raw file on disk (relative to a configured storage root)
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Full extracted text — used for full-text search and as source for chunking
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # PostgreSQL full-text search vector. Generated from `content` by a DB trigger
    # (added in the migration). Allows fast keyword search with ranking.
    # TSVECTOR is a PostgreSQL-specific type — no equivalent in SQLite.
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)

    # Flexible metadata bag: page count, author, creation date from file properties, etc.
    # JSONB stores JSON as binary in PostgreSQL — faster to query than plain JSON.
    doc_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # 0.0–1.0 confidence score from the text extraction step.
    # Low scores indicate poor-quality scans or OCR issues.
    processing_quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        String(20), nullable=False, default=ProcessingStatus.pending
    )
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="documents")
    uploaded_by: Mapped["User | None"] = relationship("User", foreign_keys=[uploaded_by_id])
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    """
    A Document split into smaller pieces for the RAG pipeline.

    Why split documents? LLMs have a context window limit (e.g. 128k tokens).
    A 200-page deposition is too large to pass entirely to the LLM. Instead,
    we split it into overlapping chunks, embed each chunk as a vector, and
    retrieve only the most relevant chunks for each query.
    """

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Position of this chunk within the document (0-indexed)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # The actual text content of this chunk
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Approximate token count — used to respect LLM context window limits
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Reference to the vector in ChromaDB. Stored here so we can look up
    # the full chunk from a ChromaDB search result without a second query.
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Page number the chunk starts on — used for citation display in the UI
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
