from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    The base class that every database model inherits from.

    Think of this like a shared TypeScript interface — every model that
    extends Base gets registered with SQLAlchemy so it knows what tables
    to create and query. Alembic also uses it to autogenerate migrations.
    """

    pass
