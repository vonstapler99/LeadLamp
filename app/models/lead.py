"""
Lead ORM model.

This file defines how the "leads" table looks in PostgreSQL.
It is used by SQLAlchemy and Alembic (for migrations).
"""

from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Lead(Base):
    """
    SQLAlchemy model mapped to the "leads" table.

    Important:
    - This is a persistence model (DB table structure).
    - It is different from Pydantic schemas used for request/response validation.
    """

    # Explicit table name in the database.
    __tablename__ = "leads"

    # UUID primary key.
    # - as_uuid=True makes SQLAlchemy return Python uuid.UUID objects.
    # - default=uuid.uuid4 generates a new UUID in Python when creating a row.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Required phone number for the lead.
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)

    # Optional first name.
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Optional last name.
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Optional query.
    query: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status starts as PENDING unless explicitly provided.
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")

    # UTC timestamp for when the row is created.
    # We use a callable so the current time is evaluated per row insert.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
