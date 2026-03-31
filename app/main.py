from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.lead import LeadCreate
from app.services.lead_service import LeadService

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
