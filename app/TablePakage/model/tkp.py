# app/products/model/tkp.py
from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class TKP(Base):
    __tablename__ = "tkp_database"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    file = Column(String(512))  # Путь к файлу
    file_url = Column(Text)  # URL файла
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"),
                        nullable=False)  # Связь через внешний ключ
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь с параметрами
    product = relationship("Product", back_populates="tkp_templates")
