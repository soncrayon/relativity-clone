from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Workspace(Base):
    """
    A Workspace is the top-level container for documents — equivalent to a
    "matter" or "case" in real eDiscovery tools. All documents, permissions,
    and AI queries are scoped to a workspace.
    """

    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    documents: Mapped[list["Document"]] = relationship("Document", back_populates="workspace")
    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_id])
