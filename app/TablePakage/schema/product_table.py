from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductTableCreate(BaseModel):
    product_id: int
    name: str = Field(min_length=1, max_length=255)


class ProductTableUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ProductTableVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_table_id: int
    version_number: int
    original_filename: str
    is_current: bool
    uploaded_at: datetime


class ProductTableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    name: str
    physical_table_name: str | None
    created_at: datetime