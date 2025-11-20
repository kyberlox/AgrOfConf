"""
Pydantic schemas for SaveOfConf module
"""

from .product import Product, ProductCreate, ProductUpdate
from .parameter_type import ParameterType, ParameterTypeCreate, ParameterTypeUpdate
from .parameter import Parameter, ParameterCreate, ParameterUpdate
from .specification_type import SpecificationType, SpecificationTypeCreate, SpecificationTypeUpdate
from .specification import Specification, SpecificationCreate, SpecificationUpdate

__all__ = [
    "Product",
    "ProductCreate",
    "ProductUpdate",
    "ParameterType",
    "ParameterTypeCreate",
    "ParameterTypeUpdate",
    "Parameter",
    "ParameterCreate",
    "ParameterUpdate",
    "SpecificationType",
    "SpecificationTypeCreate",
    "SpecificationTypeUpdate",
    "Specification",
    "SpecificationCreate",
    "SpecificationUpdate"
]