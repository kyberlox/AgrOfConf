from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class ProductTableVersion(Base):
    __tablename__ = "product_table_versions"

    id = Column(Integer, primary_key=True)
    product_table_id = Column(Integer, ForeignKey("product_tables.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    original_filename = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=False)
    is_current = Column(Boolean, nullable=False, default=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    table = relationship("ProductTable", back_populates="versions")
