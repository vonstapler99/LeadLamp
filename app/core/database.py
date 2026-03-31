from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# create_engine configures the SQLAlchemy engine and connection pool.
# Important: this is lazy and does NOT immediately open a real DB connection.
# A real connection is opened only when the first query/session checkout occurs.
engine = create_engine(settings.database_url, future=True)

# SessionLocal is a factory that creates Session objects.
# We create one Session per request using the get_db dependency below.
SessionLocal = sessionmaker(
    # Keep transactions explicit. We call commit/rollback ourselves in services.
    autocommit=False,
    # Keep pending changes in memory until needed. Common production default.
    autoflush=False,
    # Bind this session factory to our PostgreSQL engine.
    bind=engine,
    # Explicitly use sqlalchemy.orm.Session class.
    class_=Session,
)

# Base is the parent class for all ORM models (e.g., Lead).
# Alembic reads Base.metadata to know which tables should exist.
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for request-scoped DB sessions.

    Lifecycle:
    1) Create a Session.
    2) Yield it to the route/service code.
    3) Always close it in finally (success or error).
    """
    # Acquire a Session instance from the factory.
    db = SessionLocal()
    try:
        # Hand session to request handler.
        yield db
    finally:
        # Guaranteed cleanup to release the connection back to the pool.
        db.close()
