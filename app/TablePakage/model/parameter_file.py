from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class ParameterFile(Base):
    """Файлы (изображения/документы) параметра типа «Файл» (Drawing).

    Для такого параметра файлы выступают в роли его значений: пользователь
    загружает несколько файлов, а функция выбора (formula_config.func) возвращает
    конкретный file_url по значению зависимого параметра.
    """

    __tablename__ = "parameter_files"

    id = Column(Integer, primary_key=True, index=True)
    parameter_id = Column(Integer, ForeignKey("parameter_schemas.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    # Оригинальное имя файла (например «211.jpg») — по нему функция находит файл.
    name = Column(String(255), nullable=False)
    file_path = Column(Text)
    file_url = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())