# app/products/model/parameter_schema.py
from sqlalchemy import Column, Integer, String, Text, DateTime, func, JSON, ForeignKey, Index, UniqueConstraint, \
    Boolean, Float, event
from sqlalchemy.orm import relationship
from .database import Base


class ParameterSchema(Base):
    __tablename__ = "parameter_schemas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    transliterated_name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)  # "Table" или "Formula"
    measuring_unit = Column(Text, nullable=True)  # Единицы измерения
    visibility = Column(Boolean, default=True)  # Видимость для пользователя
    required_type = Column(Text, default='list')  # Тип данных для типа "Formula"
    table_name = Column(String(255))  #s Имя таблицы для типа "Table"
    field_of_view = Column(JSON, default=dict)  # Хранение JSON: {"admin": true, "user": false}
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)  # Связь через внешний ключ
    sort = Column(Float, nullable=True)

    # ORM-связь
    product = relationship("Product", back_populates="parameters")

    __table_args__ = (
        Index("idx_parameter_product_id", "product_id"),
        UniqueConstraint("product_id", "table_name", "transliterated_name", name="uq_product_parameter"),
    )
