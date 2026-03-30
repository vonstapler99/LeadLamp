from fastapi import FastAPI

app = FastAPI(title="LeadLamp API")

@app.get("/")
def read_root():
    return {"status": "online", "message": "LeadLamp Middleware is active"}

# This is the "Entry Point" for your future lead logic
@app.post("/leads/")
async def create_lead(phone_number: str):
    return {"message": f"Lead received for {phone_number}"}