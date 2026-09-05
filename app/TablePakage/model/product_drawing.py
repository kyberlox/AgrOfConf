from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class ProductDrawing(Base):
    __tablename__ = "product_drawing"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String(100), nullable=False)
    file_path = Column(Text)
    file_url = Column(Text)

    product = relationship("Product", back_populates="product_drawing")