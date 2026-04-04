from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# The engine is the low-level connection to PostgreSQL.
# pool_pre_ping=True tests the connection before using it, handling
# cases where the DB restarted while the server was running.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# SessionLocal is a factory that creates new database sessions.
# autocommit=False means we control when changes are saved (explicit commits).
# autoflush=False means SQLAlchemy won't auto-sync state before queries.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session for the duration of a request.

    Usage in a route:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    The `yield` means: open the session, hand it to the route, then run
    the `finally` block when the request finishes — even if it errored.
    This is equivalent to React's useEffect cleanup function.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
