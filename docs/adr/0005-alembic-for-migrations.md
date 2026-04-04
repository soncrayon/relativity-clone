# ADR 0005: Alembic for Database Migrations

**Status:** Accepted  
**Date:** 2026-04-04

## Context

As the project evolves, database tables and columns will need to change. We needed a strategy for managing those schema changes safely — especially in a team setting or when setting up a new machine.

## What is Alembic?

Alembic is a database migration tool for SQLAlchemy. Think of it as **git for your database schema**.

When you change a Python model (for example, add a `language` column to `Document`), Alembic can compare your Python models against what's actually in the database and **autogenerate a migration file** — a Python script containing the exact SQL needed (`ALTER TABLE documents ADD COLUMN language VARCHAR(10)`). You then apply it with `uv run alembic upgrade head`.

Each migration file is committed to git, so:

- The full history of schema changes is version-controlled
- Any developer can recreate the exact database by running all migrations from scratch
- Changes can be rolled back with `uv run alembic downgrade -1`

## Decision

Use **Alembic** for all schema changes. No manual `ALTER TABLE` statements.

## Rules

1. Never modify a migration file after it has been applied to any database
2. Every schema change starts with `uv run alembic revision --autogenerate -m "description"`
3. Review the generated file before applying — autogenerate is good but not perfect (e.g. it can't detect column renames)

## Trade-offs

- Small overhead: every schema change requires generating and committing a migration file
- Autogenerate can miss some changes (e.g. renaming a column looks like drop + add); those need manual edits to the migration file
- For a solo project, the discipline pays off when setting up a new machine or reverting a bad change
