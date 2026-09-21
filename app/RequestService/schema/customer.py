# app/requests/schema/customer.py


from pydantic import BaseModel, ConfigDict, Field

from .contact_person import ContactCreate, ContactResponse


class CustomerRequest(BaseModel):
    id: int | None = None

    organization: str | None = None
    address: str | None = None
    telephone: str | None = None
    email: str | None = None
    inn: str | None = None
    registered_address: str | None = None
    international_address: str | None = None
    website: str | None = None
    customer_type: str | None = None
    additional_information: str | None = None

    contacts: list[ContactCreate] = Field(default_factory=list)


class CustomerResponse(CustomerRequest):
    id: int

    contacts: list[ContactResponse] = Field(
        default_factory=list
    )

    model_config = ConfigDict(from_attributes=True)
