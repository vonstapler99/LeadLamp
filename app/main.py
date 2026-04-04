import logging

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.lead import LeadCreate
from app.services.lead_service import LeadService

# Basic logging so modules like notification_service can emit INFO/ERROR
# and you see them in the terminal while developing (uvicorn).
# In production you typically configure logging via dictConfig / your host's setup.
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="LeadLamp API")
lead_service = LeadService()


@app.get("/")
def read_root():
    return {"status": "online", "message": "LeadLamp Middleware is active"}


# POST with dependency injection:
# - FastAPI validates JSON into LeadCreate.
# - FastAPI injects a DB Session via get_db().
@app.post("/leads/")
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    # Delegate persistence logic to service layer.
    created = lead_service.create_lead(db=db, lead_in=lead)

    # Return JSON-safe fields for quick testing/inspection.
    return {
        "id": str(created.id),
        "phone_number": created.phone_number,
        "first_name": created.first_name,
        "last_name": created.last_name,
        "query": created.query,
        "status": created.status,
        "created_at": created.created_at.isoformat(),
    }
