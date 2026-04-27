"""
Lead ORM model.

This file defines how the "leads" table looks in PostgreSQL.
It is used by SQLAlchemy and Alembic (for migrations).
"""

from datetime import datetime, timezone
from enum import Enum
import uuid

from sqlalchemy import DateTime, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LeadStatus(str, Enum):
    """
    Allowed lifecycle states for a lead (notification / routing pipeline).

    WHY a Python Enum (single source of truth):
    - The same names are enforced in ORM, API schemas, and business logic — no
      "magic strings" scattered as 'PENDING' vs 'pending' vs typos.
    - State-machine rules later (e.g. only NOTIFIED -> FAILED) can be written
      against these members, which IDEs and type checkers understand.

    We subclass str so each member's value is a plain string in JSON and in
    the database when stored as VARCHAR (e.g. 'PENDING').
    """

    PENDING = "PENDING"
    NOTIFIED = "NOTIFIED"
    FAILED = "FAILED"


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

    # Pipeline state: Enum in Python, still stored as strings in PostgreSQL.
    #
    # WHY native_enum=False:
    # - Keeps using a VARCHAR-style column, without
    #   introducing a separate PostgreSQL ENUM type
    # - Values in the DB remain 'PENDING', 'NOTIFIED', 'FAILED' as text.
    status: Mapped[LeadStatus] = mapped_column(
        SAEnum(LeadStatus, native_enum=False, length=50),
        nullable=False,
        default=LeadStatus.PENDING,
    )

    # UTC timestamp for when the row is created.
    # We use a callable so the current time is evaluated per row insert.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
