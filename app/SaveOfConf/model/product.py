from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    manufacturer = Column(String(100))
    image = Column(String(255))

    parameters = relationship("Parameter", back_populates="product")