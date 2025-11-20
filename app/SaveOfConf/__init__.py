"""
SaveOfConf module for product management
"""

from .router.product import router as product_router
from .router.parameter_type import router as parameter_type_router
from .router.parameter import router as parameter_router
from .router.specification_type import router as specification_type_router
from .router.specification import router as specification_router

__all__ = ["product_router", "parameter_type_router", "parameter_router", "specification_type_router", "specification_router"]
__version__ = "1.0.0"