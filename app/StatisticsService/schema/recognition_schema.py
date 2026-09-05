from typing import Dict, Optional, Any
from datetime import datetime

from pydantic import BaseModel

class RecognitionData(BaseModel):
    """Модель данных для статистики распознавания ОЛ."""
    product_id: int
    user_id: int
    product_name: str
    parameters: Dict[str, Any]
    product_description: str
    product_manufacturer: str
    product_image_url: str
    user_uuid: str
    user_fio: str
    user_email: str
    user_directorate: str
    user_work_position: str
    user_office: str
    user_department: str
    user_work_city: str
    total_coast: float


class RecognitionResponse(BaseModel):
    """Ответ при сохранении / удалении."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None