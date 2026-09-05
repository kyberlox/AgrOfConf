# app/products/model/parameter_block.py
from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Index, UniqueConstraint
from .database import Base


class ParameterBlock(Base):
    """Блок параметров продукта (например, «Конструкция», «Контактные данные»).

    Параметры (ParameterSchema) привязываются к блоку через поле block_id.
    Блоки одного продукта упорядочиваются полем sort.
    """
    __tablename__ = "parameter_blocks"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    sort = Column(Float, nullable=True)
    # Свойства блока, применяемые ко всем его параметрам.
    # Например: {"editable": false, "visibility": true} — параметры видимы,
    # но недоступны для выбора пользователем.
    properties = Column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint("product_id", "name", name="uq_product_block_name"),
        Index("idx_block_product_id", "product_id"),
    )