# ADR 0006: PostgreSQL Schema Design Choices

**Status:** Accepted  
**Date:** 2026-04-04

## Context

Several specific PostgreSQL features were chosen when designing the database models. This ADR documents those decisions together since they're all part of the same schema design pass.

---

## TSVECTOR for Full-Text Search

**Decision:** The `documents` table has a `search_vector` column of type `TSVECTOR`.

**Why:** PostgreSQL has a built-in full-text search engine. `TSVECTOR` is a pre-processed, indexed representation of a text document — it strips stop words ("the", "a"), reduces words to their roots ("running" → "run"), and stores the result in a format optimized for fast keyword search. This gives us fast keyword search without needing a separate tool like Elasticsearch.

**Trade-off:** `TSVECTOR` is PostgreSQL-specific. If we ever switched to a different database (unlikely for this project), this feature would need to be replaced.

---

## JSONB for Flexible Metadata

**Decision:** Several columns use `JSONB` instead of separate columns: `doc_metadata` on `Document`, `details` on `AuditLog`.

**Why:** Documents have different metadata depending on file type — a PDF has page count and author; an email has sender, recipient, and thread ID. Rather than creating a column for every possible field (most of which would be empty for most documents), `JSONB` stores whatever metadata is available as a flexible dictionary. PostgreSQL's `JSONB` is binary-encoded, so it can be indexed and queried efficiently.

**Trade-off:** JSON fields are less type-safe than dedicated columns. We mitigate this by defining a schema in the ingestion service rather than storing arbitrary data.

---

## Cascade Delete on Document Chunks

**Decision:** The relationship from `Document` to `DocumentChunk` uses `cascade="all, delete-orphan"`.

**Why:** A document chunk has no meaning without its parent document. If a document is deleted, all its chunks should be automatically deleted too — both from PostgreSQL and eventually ChromaDB. `delete-orphan` means SQLAlchemy will also delete chunks that are removed from the `chunks` list in Python (e.g. during re-processing). This prevents orphaned rows from accumulating.

---

## Dedicated App Database User

**Decision:** The application connects as `relativity_app` (a limited-privilege user), not as `postgres` (the superuser).

**Why:** The principle of least privilege. If the application's database credentials are ever compromised, the attacker can only read/write the `relativity` database — they cannot drop all databases, create new users, or read system tables. This is a basic but important security boundary.
