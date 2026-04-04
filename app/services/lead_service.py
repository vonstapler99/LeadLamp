"""
Lead service layer.

Why this file exists:
- Route handlers should be thin (HTTP in/out).
- Persistence and business rules belong in services for reuse and testing.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadCreate
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class LeadService:
    """
    Service object responsible for lead-related business/persistence logic.
    """

    def check_for_duplicate(self, phone_number: str) -> bool:
        """
        Return True if we should skip sending another SMS for this number right now.

        WHY a dedicated session here (not the request's db):
        - The route calls this *before* inserting the new lead; we only care about
          rows already committed by other requests (same phone in the last 5 minutes).
        - Using SessionLocal matches the requested method signature and avoids mixing
          this read with the uncommitted insert in the request transaction.

        Idempotency for blue-collar missed-call bursts: repeated pings for the same
        number should not spam the business owner's phone with identical alerts.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        db = SessionLocal()
        try:
            stmt = (
                select(Lead)
                .where(Lead.phone_number == phone_number)
                .where(Lead.created_at >= cutoff)
                .limit(1)
            )
            found = db.scalars(stmt).first() is not None
            if found:
                logger.info(
                    "Duplicate lead detected for %s, skipping notification.",
                    phone_number,
                )
            return found
        finally:
            db.close()

    def create_lead(self, db: Session, lead_in: LeadCreate) -> Lead:
        """
        Create and persist a Lead row from validated API input.

        Steps:
        1) Convert Pydantic input -> ORM model instance.
        2) Add to Session.
        3) Commit transaction.
        4) Refresh so DB-generated/default values are available on the object.
        """
        # Explicit PENDING documents intent even if the column has a default.
        db_lead = Lead(
            phone_number=lead_in.phone_number,
            first_name=lead_in.first_name,
            last_name=lead_in.last_name,
            query=lead_in.query,
            status=LeadStatus.PENDING,
        )

        # Stage for insert, then persist.
        db.add(db_lead)
        db.commit()

        # Pull server/default-populated fields (id, created_at, status) into memory.
        db.refresh(db_lead)
        return db_lead


def _build_lead_sms_message(lead: Lead) -> str:
    """
    Human-readable SMS for the business owner: who called and what they need.

    WHY include name / service (query):
    - Twilio delivers plain text; context reduces callbacks and looks professional
      when you demo “AI-driven lead automation” to a tradesperson.
    """
    parts: list[str] = ["LeadLamp: New lead."]
    name_bits = [p for p in (lead.first_name, lead.last_name) if p]
    if name_bits:
        parts.append("Name: " + " ".join(name_bits) + ".")
    if lead.query:
        parts.append("Service needed: " + lead.query + ".")
    parts.append("Reply or call back when you can.")
    return " ".join(parts)


async def process_lead_notification(
    lead_id: UUID,
    phone_number: str,
    notification_service: NotificationService,
) -> None:
    """
    Runs after the HTTP response (BackgroundTasks): send SMS, then persist status.

    WHY a fresh SessionLocal inside this function:
    - The request's Session is closed when the response goes out; ORM instances
      from that session are detached. Reusing them causes DetachedInstanceError.
    - A dedicated session for this unit of work is the standard pattern for
      FastAPI background jobs (same idea as Celery tasks opening their own DB).

    phone_number is passed from the route so we fail fast if the row was deleted;
    we still load the Lead by id for name/query and authoritative phone.
    """
    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if lead is None:
            logger.error(
                "Cannot notify: lead_id=%s not found (expected phone hint %s).",
                lead_id,
                phone_number,
            )
            return

        if lead.phone_number != phone_number:
            logger.warning(
                "phone_number mismatch for lead_id=%s (task=%s, db=%s); using DB value.",
                lead_id,
                phone_number,
                lead.phone_number,
            )

        message = _build_lead_sms_message(lead)
        ok = await notification_service.send_sms_notification(lead.phone_number, message)

        if ok:
            lead.status = LeadStatus.NOTIFIED
            db.commit()
            logger.info("Lead %s marked NOTIFIED after successful SMS.", lead_id)
        else:
            lead.status = LeadStatus.FAILED
            db.commit()
            logger.error(
                "SMS delivery failed for lead_id=%s phone=%s; status set to FAILED.",
                lead_id,
                lead.phone_number,
            )
    except Exception:
        db.rollback()
        logger.exception(
            "Unexpected error in process_lead_notification for lead_id=%s",
            lead_id,
        )
    finally:
        db.close()
