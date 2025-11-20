from sqlalchemy import Column, Integer, String, Text
from .database import Base

class SpecificationType(Base):
    __tablename__ = "specification_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)