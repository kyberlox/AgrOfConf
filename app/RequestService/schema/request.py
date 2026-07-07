# app/requests/schema/request.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RequestBase(BaseModel):
    name: str
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    image_url: Optional[str] = None