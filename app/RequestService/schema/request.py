# app/requests/schema/request.py

from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, StringConstraints, model_validator

from .contact_person import ContactCreate, ContactResponse
from .customer import CustomerCreate, CustomerResponse

NonEmptyStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class RequestCreate(BaseModel):
    # Передаётся для существующего заказчика
    customer_id: Optional[PositiveInt] = None

    # Передаётся для нового заказчика
    customer: Optional[CustomerCreate] = None

    contacts: list[ContactCreate] = Field(default_factory=list)

    organization_id: Optional[PositiveInt] = None
    request_purpose: NonEmptyStr
    description: Optional[str] = None
    construction_project: Optional[str] = None
    tkp_term: Optional[str] = None
    delivery_time: Optional[str] = None
    procedure_type: NonEmptyStr

    @model_validator(mode="after")
    def validate_customer_source(self):
        if self.customer_id is None and self.customer is None:
            raise ValueError(
                "Нужно передать customer_id существующего заказчика "
                "или customer для создания нового"
            )

        if self.customer_id is not None and self.customer is not None:
            raise ValueError(
                "Нельзя одновременно передавать customer_id и customer"
            )

        return self

class RequestUpdate(BaseModel):
    customer_id: Optional[PositiveInt] = None
    organization_id: Optional[PositiveInt] = None
    request_purpose: Optional[NonEmptyStr] = None
    description: Optional[str] = None
    construction_project: Optional[str] = None
    tkp_term: Optional[str] = None
    delivery_time: Optional[str] = None
    procedure_type: Optional[NonEmptyStr] = None

    @model_validator(mode="after")
    def validate_required_fields(self):
        for field_name in ("customer_id", "request_purpose", "procedure_type"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} не может быть null")
        return self

class RequestResponse(BaseModel):
    id: int
    user_id: int
    customer_id: int
    organization_id: Optional[int] = None
    request_purpose: Optional[str] = None
    description: Optional[str] = None
    construction_project: Optional[str] = None
    tkp_term: Optional[str] = None
    delivery_time: Optional[str] = None
    procedure_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RequestCreateResponse(BaseModel):
    id: int
    customer_id: int
    organization_id: Optional[int] = None
    request_purpose: Optional[str] = None
    description: Optional[str] = None
    construction_project: Optional[str] = None
    tkp_term: Optional[str] = None
    delivery_time: Optional[str] = None
    procedure_type: Optional[str] = None

    customer: CustomerResponse
    contacts: list[ContactResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
