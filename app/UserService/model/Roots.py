from app.TablePakage.model.database import Base
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import  relationship

class Roots(Base):
    __tablename__ = "roots"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    admin = Column(Boolean, default=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True)

    user = relationship("Users", back_populates="rootsusers")
    product = relationship("Product", back_populates="roots")
