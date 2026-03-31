"""
Lead service layer.

Why this file exists:
- Route handlers should be thin (HTTP in/out).
- Persistence and business rules belong in services for reuse and testing.
"""

from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.schemas.lead import LeadCreate


class LeadService:
    """
    Service object responsible for lead-related business/persistence logic.
    """

    def create_lead(self, db: Session, lead_in: LeadCreate) -> Lead:
        """
        Create and persist a Lead row from validated API input.

        Steps:
        1) Convert Pydantic input -> ORM model instance.
        2) Add to Session.
        3) Commit transaction.
        4) Refresh so DB-generated/default values are available on the object.
        """
        # Convert request schema data into the DB model shape.
        db_lead = Lead(
            phone_number=lead_in.phone_number,
            first_name=lead_in.first_name,
            last_name=lead_in.last_name,
            query=lead_in.query,
        )

        # Stage for insert, then persist.
        db.add(db_lead)
        db.commit()

        # Pull server/default-populated fields (id, created_at, status) into memory.
        db.refresh(db_lead)
        return db_lead
