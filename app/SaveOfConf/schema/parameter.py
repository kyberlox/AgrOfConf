from pydantic import BaseModel
from typing import Optional, Any, Dict, List

class ParameterBase(BaseModel):
    name: str
    description: Optional[str] = None
    product_id: int
    parameter_type_id: int
    value: Optional[Dict[str, Any]] = None  # BSON-подобные данные

class ParameterCreate(ParameterBase):
    pass

class ParameterUpdate(ParameterBase):
    pass

class Parameter(ParameterBase):
    id: int

    class Config:
        orm_mode = True