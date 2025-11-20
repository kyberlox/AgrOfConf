from pydantic import BaseModel
from typing import Optional

class ParameterTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

class ParameterTypeCreate(ParameterTypeBase):
    pass

class ParameterTypeUpdate(ParameterTypeBase):
    pass

class ParameterType(ParameterTypeBase):
    id: int

    class Config:
        orm_mode = True