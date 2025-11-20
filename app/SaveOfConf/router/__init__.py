"""
FastAPI routers for SaveOfConf module
"""

from .product import router as product_router
from .parameter_type import router as parameter_type_router
from .product import router as product_router
from .specification_type import router as specification_type_router
from .specification import router as specification_router

__all__ = ["product_router", "parameter_type_router", "product_router", "specification_type_router", "specification_router"]