# app/requests/schema/customer.py

from typing import Annotated, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


NonEmptyStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class CustomerBase(BaseModel):
    organization: Optional[str] = None
    address: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    inn: Optional[str] = None
    registered_address: Optional[str] = None
    international_address: Optional[str] = None
    website: Optional[str] = None
    customer_type: Optional[str] = None
    additional_information: Optional[str] = None
    visibility: bool = True
    field_of_view: dict[str, Any] = Field(default_factory=dict)


class CustomerCreate(CustomerBase):
    organization: NonEmptyStr


class CustomerResponse(CustomerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
