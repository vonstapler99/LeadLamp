from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# create_engine is lazy: it configures the engine/pool now and opens a real DB
# connection only when the first query/session checkout happens.
engine = create_engine(settings.database_url, future=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides one DB session per request and ensures
    cleanup even if an exception is raised.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
