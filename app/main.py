from fastapi import BackgroundTasks, Depends, FastAPI, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.lead import LeadCreate, LeadRead
from app.services.lead_service import LeadService, process_lead_notification
from app.services.notification_service import NotificationService

# Logging is not configured here: production apps use uvicorn's --log-config,
# dictConfig in a dedicated module, or the host's log aggregation. Libraries
# call logging.getLogger(__name__) and rely on that root configuration.

app = FastAPI(title="LeadLamp API")
lead_service = LeadService()

# Single shared instance with validated settings; passed into background tasks.
# WHY construct here: same pattern as LeadService — one object per process, injected
# into async workers so tests can swap a fake NotificationService later if needed.
notification_service = NotificationService(settings=settings)


@app.get("/")
def read_root():
    return {"status": "online", "message": "LeadLamp Middleware is active"}


# 202 Accepted: we persisted the lead immediately; SMS + status update happen after the response.
# That keeps the API responsive and matches “async reliability” — the client does not wait on Twilio.
@app.post(
    "/leads/",
    response_model=LeadRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_lead(
    lead: LeadCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Idempotency: if this number already created a lead in the last 5 minutes,
    # we still store this row for audit but do not enqueue another SMS.
    skip_notification = lead_service.check_for_duplicate(lead.phone_number)

    created = lead_service.create_lead(db=db, lead_in=lead)

    if not skip_notification:
        # FastAPI runs this after the response body is sent; failures there do not
        # change the HTTP status the client already received (monitor logs / metrics).
        background_tasks.add_task(
            process_lead_notification,
            created.id,
            created.phone_number,
            notification_service,
        )

    return LeadRead.model_validate(created)
