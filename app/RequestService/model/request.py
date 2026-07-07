# app/requests/model/request.py

from sqlalchemy import Column, Integer, String, Text, DateTime, func, Sequence, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from .database import Base

request_num_seq = Sequence("request_num_seq", start=1)


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    request_num = Column(Integer, request_num_seq, server_default=request_num_seq.next_value(), unique=True,
                         nullable=False)
    status = Column(String, nullable=False, default="Открыт")
    ol_count = Column(Integer, nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"),
                         nullable=True)  # Связь через внешний ключ
    organization_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"),
                             nullable=True)  # Связь через внешний ключ
    request_purpose = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    edited_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    construction_project = Column(Text, nullable=True)
    tkp_term = Column(DateTime(timezone=True), nullable=True)
    delivery_time = Column(DateTime(timezone=True), nullable=True)
    procedure_type = Column(String, nullable=False)
    selection_ids = Column(JSON, nullable=True)
    user_id = Column(Integer, ForeignKey("requests.user_id", ondelete="RESTRICT"),
                     nullable=False)  # Связь через внешний ключ
    visibility = Column(Boolean, default=True)  # Видимость для пользователя
    field_of_view = Column(JSON, default=dict)  # Хранение JSON: {"admin": true, "user": false}
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)  # Связь через внешний ключ

    # Связь
    customer = relationship("Customer", foreign_keys=[customer_id], back_populates="customer_requests")
    organization = relationship("Customer", foreign_keys=[organization_id], back_populates="organization_requests")
    user = relationship("User")
    product = relationship("Product")
