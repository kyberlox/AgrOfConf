from typing import Dict, Optional, Any
from datetime import datetime

from pydantic import BaseModel

class SelectionData(BaseModel):
    """Модель данных для статистики подбора ОЛ."""
    product_id: int
    user_id: int
    product_name: str
    date_search: datetime
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


class SelectionResponse(BaseModel):
    """Ответ при сохранении / удалении."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class PeriodStat(BaseModel):
    """Статистика за период: текущее значение, предыдущее, разница."""
    current: int
    previous: int
    diff: int


class StatisticsResponse(BaseModel):
    """Ответ со статистикой по документам."""
    month: PeriodStat
    day: PeriodStat
    year: PeriodStat
    total: int