from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Pull in our app's settings (reads DATABASE_URL from .env)
from app.core.config import settings

# Import all models so Alembic's autogenerate can detect table changes.
# Without these imports, Alembic would generate empty migrations.
import app.models  # noqa: F401 — side-effect import registers all models

# Base.metadata contains the "desired" schema (what our Python models describe).
# Alembic diffs this against the "current" schema in the DB to generate migrations.
from app.models.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Generate migration SQL without connecting to the DB.
    Useful for reviewing what changes will be made before applying them.
    Run with: uv run alembic upgrade head --sql
    """
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Apply migrations directly to the connected database.
    This is what `uv run alembic upgrade head` does.
    """
    configuration = config.get_section(config.config_ini_section, {})
    # Override the URL from alembic.ini with the one from our .env
    configuration["sqlalchemy.url"] = settings.database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

