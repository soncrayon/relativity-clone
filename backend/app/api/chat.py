"""
Chat API — workspace-scoped RAG chat endpoints.

  POST   /workspaces/{id}/chat          → ask a question, get an AI answer
  GET    /workspaces/{id}/chat/history  → list past messages in this workspace
  GET    /workspaces/{id}/chat/{msg_id}/citations → citations for one AI message

All routes are scoped under /workspaces/{workspace_id}/chat so that
conversation history and retrieval are always tied to a specific workspace —
the same workspace that scopes document access and (in Phase 3) RBAC checks.

The POST endpoint persists both the user question and the AI answer as
ChatMessage rows so history survives server restarts.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chat import ChatMessage, MessageRole
from app.models.workspace import Workspace
from app.services import rag

router = APIRouter(
    prefix="/workspaces/{workspace_id}/chat",
    tags=["chat"],
)


# ── request / response shapes ──────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str


class CitationOut(BaseModel):
    marker: str
    chunk_id: str
    document_id: int
    document_filename: str
    chunk_index: int
    text_snippet: str
    page_number: int | None = None


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    citations: list[CitationOut] | None = None
    confidence: float | None = None
    chunks_retrieved: int | None = None
    created_at: str

    @classmethod
    def from_orm(cls, msg: ChatMessage) -> "ChatMessageOut":
        citations_out = None
        if msg.citations:
            citations_out = [CitationOut(**c) for c in msg.citations]
        return cls(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            citations=citations_out,
            confidence=msg.confidence,
            chunks_retrieved=msg.chunks_retrieved,
            created_at=msg.created_at.isoformat(),
        )


# ── helpers ────────────────────────────────────────────────────────────────────

def _get_workspace_or_404(workspace_id: int, db: Session) -> Workspace:
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return ws


# ── endpoints ──────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def ask(
    workspace_id: int,
    body: AskRequest,
    db: Session = Depends(get_db),
) -> ChatMessageOut:
    """
    Ask a question against the documents in this workspace.

    Runs the full RAG pipeline:
      1. Embed the question and retrieve semantically similar chunks from ChromaDB
      2. Pass chunks as context to the configured LLM provider (default: Ollama)
      3. Validate citations — drop any that don't reference a real chunk
      4. Persist both the user question and AI answer as ChatMessage rows
      5. Return the AI message (with citations) to the caller

    Requires documents to have been uploaded, processed, and chunked first.
    If no indexed chunks exist for this workspace, returns a helpful error message
    rather than an empty answer.
    """
    _get_workspace_or_404(workspace_id, db)

    if not body.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty.")

    # Persist the user's question
    user_msg = ChatMessage(
        workspace_id=workspace_id,
        role=MessageRole.user,
        content=body.question.strip(),
    )
    db.add(user_msg)
    db.commit()

    # Run the RAG pipeline
    try:
        response = rag.ask(
            question=body.question.strip(),
            workspace_id=workspace_id,
            db=db,
        )
    except Exception as exc:
        # Surface LLM connection errors (e.g. Ollama not running) as a 502
        # so the frontend can show a meaningful error instead of a spinner.
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider error: {exc}",
        ) from exc

    # Serialise validated citations to plain dicts for JSONB storage
    citations_json = [
        {
            "marker": c.marker,
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "document_filename": c.document_filename,
            "chunk_index": c.chunk_index,
            "text_snippet": c.text_snippet,
            "page_number": c.page_number,
        }
        for c in response.citations
    ]

    # Persist the AI answer
    assistant_msg = ChatMessage(
        workspace_id=workspace_id,
        role=MessageRole.assistant,
        content=response.answer,
        citations=citations_json if citations_json else None,
        confidence=response.confidence,
        chunks_retrieved=response.chunks_retrieved,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatMessageOut.from_orm(assistant_msg)


@router.get("/history")
def get_history(
    workspace_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[ChatMessageOut]:
    """
    Return the most recent messages in this workspace, oldest first.

    Both user questions and AI answers are included so the frontend can
    render a full conversation thread. `limit` caps the response to avoid
    returning thousands of messages in long-running workspaces.
    """
    _get_workspace_or_404(workspace_id, db)

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.workspace_id == workspace_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    return [ChatMessageOut.from_orm(m) for m in messages]


@router.get("/{message_id}/citations")
def get_citations(
    workspace_id: int,
    message_id: int,
    db: Session = Depends(get_db),
) -> list[CitationOut]:
    """
    Return the citations attached to a specific AI message.

    Used by the frontend's citation click handler — when a user clicks [1]
    in the answer text, the UI fetches the citation details to navigate to
    and highlight the source chunk in the document viewer.
    """
    msg = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.id == message_id,
            ChatMessage.workspace_id == workspace_id,
            ChatMessage.role == MessageRole.assistant,
        )
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found.")

    if not msg.citations:
        return []

    return [CitationOut(**c) for c in msg.citations]
