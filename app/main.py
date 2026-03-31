from fastapi import FastAPI

from app.schemas.lead import LeadCreate

app = FastAPI(title="LeadLamp API")


@app.get("/")
def read_root():
    return {"status": "online", "message": "LeadLamp Middleware is active"}


# POST with a Pydantic parameter: FastAPI reads the JSON body, validates it,
# and passes a LeadCreate instance to your function (or returns 422 if invalid).
@app.post("/leads/")
async def create_lead(lead: LeadCreate):
    # model_dump() turns the model into a plain dict (good for logging, APIs, DB layers).
    print(lead.model_dump())
    return {"message": "Lead received", "phone_number": lead.phone_number}
