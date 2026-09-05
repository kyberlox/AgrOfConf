# app/requests/schema/contact_person.py

from typing import Annotated, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


NonEmptyStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class ContactCreate(BaseModel):
    full_name: NonEmptyStr
    job_title: Optional[str] = None
    work_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    email: Optional[str] = None
    visibility: bool = True
    field_of_view: dict[str, Any] = Field(default_factory=dict)


class ContactResponse(ContactCreate):
    id: int
    customer_id: int

    model_config = ConfigDict(from_attributes=True)
