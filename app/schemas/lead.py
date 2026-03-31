"""
Request-body shapes for creating a lead.

Pydantic models describe "what valid JSON looks like" before your route logic runs.
FastAPI uses them to parse incoming HTTP JSON into normal Python objects.
"""

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    """
    Data a client sends when creating a new lead (e.g. POST /leads/).

    Fields with a default (like None) are optional in the JSON body.
    Fields without a default (phone_number) are required.
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
