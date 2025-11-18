"""
Pydantic schemas for SaveOfConf module
"""

from .product import Product, ProductCreate, ProductUpdate

__all__ = [
    "Product",
    "ProductCreate",
    "ProductUpdate"
]