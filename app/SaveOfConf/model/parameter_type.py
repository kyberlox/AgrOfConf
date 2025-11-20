from sqlalchemy import Column, Integer, String, Text
from .database import Base

class ParameterType(Base):
    __tablename__ = "parameter_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)