import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(str, enum.Enum):
    """
    The three access levels in the system, matching real Relativity's RBAC model.
    Using str+Enum means the role is stored as a readable string in the DB
    ("admin", "reviewer", "viewer") not a number — easier to debug.
    """

    admin = "admin"        # Full access: manage users, groups, workspaces
    reviewer = "reviewer"  # Can view documents and submit AI chat queries
    viewer = "viewer"      # Read-only: can view documents but not use AI chat


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Never store plain-text passwords. hashed_password stores the bcrypt hash.
    # We'll add the hashing logic in Phase 3 when we wire up auth.
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False, default=UserRole.viewer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # server_default=func.now() means PostgreSQL sets the timestamp, not Python.
    # This is more reliable because it uses the DB server's clock.
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationship: a User can belong to many Groups.
    # back_populates="members" links to the `members` attribute on the Group model.
    groups: Mapped[list["Group"]] = relationship(
        "Group", secondary="user_groups", back_populates="members"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")
