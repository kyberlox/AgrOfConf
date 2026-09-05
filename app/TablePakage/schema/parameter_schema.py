# app/products/schema/parameter_schema.py
import json
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any

FIELD_OF_VIEWS = ['codeparam']

class ParameterSchemaBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str  # "Table" or "Formula"
    measuring_unit: Optional[str] = None
    table_name: Optional[str] = None
    visibility: Optional[bool] = True
    editable: Optional[bool] = True
    required_type: Optional[str] = 'list'
    # field_of_view: Optional[Dict[str, bool]] = None
    field_of_view: Optional[str] = None
    # Конфигурация расчёта (новая система формул):
    # {"func": "...", "validate": "...", "type": "formula"}
    formula_config: Optional[Dict[str, Any]] = None
    product_id: int
    sort: float

    # Поле field_of_view исторически хранилось как Dict[str, bool],
    # теперь ожидается строка. Приводим словарь к JSON-строке,
    # чтобы сериализация старых записей не падала с 500.
    @validator('field_of_view', pre=True, always=True)
    def normalize_field_of_view(cls, value):
        if value is None:
            return None
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return value


class ParameterSchemaCreate(ParameterSchemaBase):
    pass


class ParameterSchemaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    measuring_unit: Optional[str] = None
    visibility: Optional[bool] = True
    editable: Optional[bool] = True
    required_type: Optional[str] = 'list'
    table_name: Optional[str] = None
    # field_of_view: Optional[Dict[str, bool]] = None
    field_of_view: Optional[str] = None
    formula_config: Optional[Dict[str, Any]] = None
    product_id: Optional[int] = None
    sort: Optional[float] = True

    # @validator('field_of_view', pre=True, always=True)
    # def validate_operation(cls, value):
    #     if value is None:
    #         return {field: False for field in FIELD_OF_VIEWS}
    #     if not all(key in FIELD_OF_VIEWS for key in value):
    #         raise ValueError(f"Недопустимый формульный тип!")
    #     for field in FIELD_OF_VIEWS:
    #         if field not in value:
    #             value[field] = False
    #     return value


class ParameterSchemaResponse(ParameterSchemaBase):
    id: int
    transliterated_name: str

    class Config:
        from_attributes = True
