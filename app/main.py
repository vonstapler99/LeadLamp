from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.lead import LeadCreate, LeadRead
from app.services.lead_service import LeadService

# Logging is not configured here: production apps use uvicorn's --log-config,
# dictConfig in a dedicated module, or the host's log aggregation. Libraries
# call logging.getLogger(__name__) and rely on that root configuration.
#
# When you add SMS to a route, inject NotificationService with validated settings, e.g.:
#   def get_notification_service() -> NotificationService:
#       return NotificationService(settings=settings)
#   ... endpoint(..., svc: NotificationService = Depends(get_notification_service))

app = FastAPI(title="LeadLamp API")
lead_service = LeadService()


@app.get("/")
def read_root():
    return {"status": "online", "message": "LeadLamp Middleware is active"}


# POST with dependency injection:
# - FastAPI validates JSON into LeadCreate.
# - FastAPI injects a DB Session via get_db().
@app.post("/leads/", response_model=LeadRead)
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    # Delegate persistence logic to service layer.
    created = lead_service.create_lead(db=db, lead_in=lead)

    # LeadRead validates ORM -> API shape and documents OpenAPI (including status enum).
    return LeadRead.model_validate(created)
