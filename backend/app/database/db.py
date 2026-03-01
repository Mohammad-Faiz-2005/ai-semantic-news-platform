"""
Database engine, session factory, and Base class setup.

SQLAlchemy async-compatible session management.
The get_db() function is used as a FastAPI dependency
to provide a scoped session per request.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


# ── Engine ────────────────────────────────────────────────────────────────────

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,    # Test connections before using (handles stale connections)
    pool_size=10,          # Number of persistent connections in the pool
    max_overflow=20,       # Extra connections allowed beyond pool_size
    echo=False,            # Set True to log all SQL statements (debug only)
)


# ── Session Factory ───────────────────────────────────────────────────────────

SessionLocal = sessionmaker(
    autocommit=False,   # Explicit commits required
    autoflush=False,    # Manual flush control
    bind=engine,
)


# ── Declarative Base ──────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    All models must inherit from this class.
    """
    pass


# ── Dependency ────────────────────────────────────────────────────────────────

def get_db():
    """
    FastAPI dependency that provides a database session per request.

    Usage in route:
        def my_route(db: Session = Depends(get_db)):
            ...

    Ensures the session is always closed after the request,
    even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()