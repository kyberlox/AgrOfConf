# app/requests/schema/request.py

from pydantic import BaseModel, ConfigDict

from .customer import CustomerRequest, CustomerResponse


class RequestData(BaseModel):
    request_purpose: str
    description: str | None = None
    construction_project: str | None = None
    tkp_term: str | None = None
    delivery_time: str | None = None
    procedure_type: str


class RequestDataUpdate(BaseModel):
    request_purpose: str | None = None
    description: str | None = None
    construction_project: str | None = None
    tkp_term: str | None = None
    delivery_time: str | None = None
    procedure_type: str | None = None


class RequestCreate(BaseModel):
    request: RequestData

    customer: CustomerRequest
    organization: CustomerRequest
    end_customer: CustomerRequest | None = None


class RequestUpdate(BaseModel):
    request: RequestDataUpdate | None = None

    customer: CustomerRequest | None = None
    organization: CustomerRequest | None = None
    end_customer: CustomerRequest | None = None


class RequestResponse(BaseModel):
    id: int
    request_num: int
    status: str | None = None

    request: RequestData

    customer: CustomerResponse | None = None
    organization: CustomerResponse | None = None
    end_customer: CustomerResponse | None = None

    model_config = ConfigDict(from_attributes=True)
