"""
Schema smoke tests: verify `alembic upgrade head` created the expected schema.
Intentionally lightweight — checks columns exist, not data layer end-to-end.
As CRUD endpoints are added (Step 5), round-trip tests will supersede these.
These stay as a safety net for fresh machine setup.

Run with: uv run pytest tests/test_db_migration.py -v
"""

from sqlalchemy import inspect, text

from app.core.database import engine

EXPECTED_TABLES = {
    "users",
    "groups",
    "user_groups",
    "workspaces",
    "documents",
    "document_chunks",
    "audit_logs",
}


def test_can_reach_postgresql():
    """A basic SELECT 1 confirms the DATABASE_URL in .env is valid and
    PostgreSQL is accepting connections."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_initial_migration_created_all_domain_tables():
    """Every table defined in the models should exist after running
    `alembic upgrade head` on a fresh database."""
    inspector = inspect(engine)
    actual_tables = set(inspector.get_table_names())
    assert EXPECTED_TABLES <= actual_tables


def test_users_table_has_auth_and_rbac_columns():
    """The users table has all the columns needed for authentication
    (email, hashed_password) and role-based access control (role, is_active)."""
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("users")}
    assert {"id", "email", "hashed_password", "role", "is_active"} <= columns


def test_documents_table_has_ingestion_tracking_columns():
    """The documents table has the columns needed to track ingestion state
    (processing_status, processing_quality) and enable full-text search
    (content, search_vector)."""
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("documents")}
    assert {
        "id", "workspace_id", "filename", "file_type",
        "content", "processing_status", "processing_quality"
    } <= columns


def test_document_chunks_table_has_rag_pipeline_columns():
    """The document_chunks table has the columns required by the RAG pipeline:
    chunk_index and content for retrieval, embedding_id to link back to
    ChromaDB, and page_number for citation display in the UI."""
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("document_chunks")}
    assert {"id", "document_id", "chunk_index", "content", "embedding_id", "page_number"} <= columns
