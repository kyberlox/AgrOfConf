from pydantic import BaseModel
from typing import Optional, Any, Dict

class SpecificationBase(BaseModel):
    name: str
    description: Optional[str] = None
    parameter_id: int
    specification_type_id: int
    value: Optional[Dict[str, Any]] = None  # JSON данные

class SpecificationCreate(SpecificationBase):
    pass

class SpecificationUpdate(SpecificationBase):
    pass

class Specification(SpecificationBase):
    id: int

    class Config:
        orm_mode = True