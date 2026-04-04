# Import all models here so Alembic's autogenerate can detect them.
# If a model isn't imported before Alembic runs, it won't appear in migrations.
# This is equivalent to a barrel file (index.ts) in the frontend.
from app.models.audit import AuditLog
from app.models.base import Base
from app.models.document import Document, DocumentChunk
from app.models.group import Group, user_groups
from app.models.user import User, UserRole
from app.models.workspace import Workspace

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Group",
    "user_groups",
    "Workspace",
    "Document",
    "DocumentChunk",
    "AuditLog",
]
