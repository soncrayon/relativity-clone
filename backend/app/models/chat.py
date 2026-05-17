"""
ChatMessage model — persists conversation history for the RAG chat feature.

Each message is either a user question or an AI answer, linked to a workspace.
Storing history in PostgreSQL (rather than in-memory or client-side) means:
  - Conversations survive server restarts
  - The audit trail (Phase 3) can reference specific messages
  - The UI can show history across sessions

Citations are stored as JSONB — a list of ValidatedCitation dicts serialised
at write time. This avoids a separate citations table while keeping the data
queryable via PostgreSQL's JSON operators if needed later.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MessageRole(str, enum.Enum):
    user = "user"      # The question typed by the human
    assistant = "assistant"  # The AI's answer


class ChatMessage(Base):
    """
    A single turn in a workspace conversation.

    Pairs of (user, assistant) messages form a conversation thread.
    All messages are scoped to a workspace — the same workspace that
    scopes document retrieval — so the AI can only cite documents in
    the same workspace as the conversation.
    """

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # "user" or "assistant"
    role: Mapped[MessageRole] = mapped_column(String(20), nullable=False)

    # The message content — question text for user, answer text for assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # For assistant messages: the validated citations as a JSON list.
    # Each entry mirrors ValidatedCitation: {marker, chunk_id, document_id,
    # document_filename, chunk_index, text_snippet, page_number}
    # Null for user messages.
    citations: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # 0.0–1.0 confidence score from the LLM provider. Null for user messages.
    confidence: Mapped[float | None] = mapped_column(nullable=True)

    # How many chunks were retrieved from ChromaDB for this response.
    # Useful for debugging retrieval quality. Null for user messages.
    chunks_retrieved: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    workspace: Mapped["Workspace"] = relationship("Workspace")
