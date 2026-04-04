"""
Request-body shapes for creating a lead.

Pydantic models describe "what valid JSON looks like" before your route logic runs.
FastAPI uses them to parse incoming HTTP JSON into normal Python objects.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.lead import LeadStatus


class LeadCreate(BaseModel):
    """
    Data a client sends when creating a new lead (e.g. POST /leads/).

    Fields with a default (like None) are optional in the JSON body.
    Fields without a default (phone_number) are required.

    Status is not part of the create payload: the server owns initial state
    (typically LeadStatus.PENDING) until notifications or retries run.
    """

    # Required: every lead must identify how to reach the customer.
    phone_number: str = Field(
        ...,
        description="Caller or contact phone number (E.164 or local format from your client).",
    )

    # Optional: caller may not leave a name on a missed call.
    first_name: str | None = Field(default=None, description="Contact first name, if known.")
    last_name: str | None = Field(default=None, description="Contact last name, if known.")

    # Optional: short description of the job (e.g. 'leaking water heater').
    query: str | None = Field(
        default=None,
        description="What the customer needs fixed or quoted.",
    )


class LeadRead(BaseModel):
    """
    Shape returned to clients after a lead is created or fetched.

    WHY status uses LeadStatus here too:
    - Same Enum as the ORM: API responses only advertise valid states.
    - FastAPI / OpenAPI document allowed values for clients and tools.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phone_number: str
    first_name: str | None
    last_name: str | None
    query: str | None
    status: LeadStatus
    created_at: datetime
