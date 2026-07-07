# app/requests/model/customer.py

from sqlalchemy import Column, Integer, String, Text, DateTime, func, Sequence, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from .database import Base



class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    organization = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    telephone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    inn = Column(String, nullable=True)
    registered_address = Column(Text, nullable=True)
    international_address = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    customer_type = Column(String, nullable=True)
    additional_information = Column(Text, nullable=True)
    visibility = Column(Boolean, default=True)  # Видимость для пользователя
    field_of_view = Column(JSON, default=dict)  # Хранение JSON: {"admin": true, "user": false}


    # Связь

