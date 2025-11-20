from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

class Specification(Base):
    __tablename__ = "specifications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    parameter_id = Column(Integer, ForeignKey("parameters.id"), nullable=False)
    specification_type_id = Column(Integer, ForeignKey("specification_types.id"), nullable=False)
    value = Column(JSON)  # JSON-хранение данных спецификации

    # Опциональные отношения
    parameter = relationship("Parameter", back_populates="specifications")
    specification_type = relationship("SpecificationType")