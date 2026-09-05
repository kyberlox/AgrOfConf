from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class ProductTable(Base):
    __tablename__ = "product_tables"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    physical_table_name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ORM-связь
    product = relationship("Product", back_populates="product_tables")
    versions = relationship("ProductTableVersion", back_populates="table", cascade="all, delete-orphan",
    passive_deletes=True)

