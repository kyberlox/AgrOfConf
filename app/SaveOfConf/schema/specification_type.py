from pydantic import BaseModel
from typing import Optional

class SpecificationTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

class SpecificationTypeCreate(SpecificationTypeBase):
    pass

class SpecificationTypeUpdate(SpecificationTypeBase):
    pass

class SpecificationType(SpecificationTypeBase):
    id: int

    class Config:
        orm_mode = True