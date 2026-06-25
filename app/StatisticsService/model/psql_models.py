from app.TablePakage.model.database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB

class RecognitionModel(Base):
    __tablename__ = "recognition_model"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    product_info = Column(JSONB, nullable=False)
    user_info = Column(JSONB, nullable=False)
    parameters = Column(JSONB, nullable=False)
    total_coast = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)


class SelectionModel(Base):
    __tablename__ = "selection_model"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    product_info = Column(JSONB, nullable=False)
    user_info = Column(JSONB, nullable=False)
    parameters = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False)