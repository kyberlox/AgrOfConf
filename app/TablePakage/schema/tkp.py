# app/products/schema/tkp.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TKPBase(BaseModel):
    name: str
    file_url: Optional[str] = None
    product_id: int


class TKPCreate(TKPBase):
    name: str


class TKPResponse(TKPBase):
    id: int
    file: Optional[str] = None
    file_url: Optional[str] = None
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True
