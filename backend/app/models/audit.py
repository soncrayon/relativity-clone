from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AuditLog(Base):
    """
    Immutable log of every significant action in the system.

    In legal tech, courts increasingly require that AI usage be fully auditable.
    Every query sent to the AI, every document viewed, and every login is
    recorded here. Rows are never updated or deleted — only inserted.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # user_id is nullable — system-level events (e.g. background processing)
    # don't have an associated user
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Human-readable action names, e.g.:
    # "login", "logout", "document_upload", "document_view",
    # "chat_query", "citation_click", "review_approve", "review_reject"
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # What type of thing was acted on: "document", "workspace", "chat_message", etc.
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # The ID of the specific resource (e.g. document id=42)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Free-form JSON for action-specific data:
    # For chat_query: {question, model_used, chunk_ids_retrieved}
    # For document_upload: {filename, file_type, file_size}
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Optional: track where requests came from for security investigations
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )

    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")
