from app.TablePakage.model.database import Base
from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship

class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    uuid = Column(String(255), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    last_name = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    second_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    work_phone = Column(String(255), nullable=True)
    directorate = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    work_position = Column(String(255), nullable=True)
    work_city = Column(String(255), nullable=True)
    office = Column(Integer, nullable=True)

    rootsusers = relationship("Roots", back_populates="user")

