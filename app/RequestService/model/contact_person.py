# app/requests/model/customer.py

from sqlalchemy import Column, Integer, String, Text, DateTime, func, Sequence, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from .database import Base


class ContactPerson(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(Text, nullable=False)
    job_title = Column(Text, nullable=True)
    work_phone = Column(String, nullable=True)
    mobile_phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"),
                         nullable=False)  # Связь через внешний ключ
    visibility = Column(Boolean, default=True)  # Видимость для пользователя
    field_of_view = Column(JSON, default=dict)  # Хранение JSON: {"admin": true, "user": false}

    # Связь
    customer = relationship("Customer", back_populates="contacts")
