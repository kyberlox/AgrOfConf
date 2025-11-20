from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

class Parameter(Base):
    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    parameter_type_id = Column(Integer, ForeignKey("parameter_types.id"), nullable=False)
    value = Column(JSON)  # BSON-подобное хранение данных

    # Опциональные отношения (если нужны)
    product = relationship("Product", back_populates="parameters")
    parameter_type = relationship("ParameterType")
    specifications = relationship("Specification", back_populates="parameter")