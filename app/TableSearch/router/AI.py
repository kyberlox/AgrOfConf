from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
import json
from typing import Dict, Any

from gigachat import GigaChat

router = APIRouter(prefix="/AI", tags=["GigaChat-2-Pro"])

client_id = "019cfb75-d657-765b-9e14-8d227ea7449d"
scope= "GIGACHAT_API_PERS"
API_KEY = "MDE5Y2ZiNzUtZDY1Ny03NjViLTllMTQtOGQyMjdlYTc0NDlkOmM4YzBlMWFlLWJkNDAtNDM0MC05YmUzLTFkOThmYzU0ZWRlMg=="

def rspozNAT():
    with GigaChat(credentials=API_KEY, model='название_модели') as client:
        response = client.chat("Hello, GigaChat!")
        print(response.choices[0].message.content)


@router.post("/upload_OL")
async def upload_OL(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Эндпоинт для загрузки файла.
    Принимает файл, читает его метаданные и возвращает JSON.
    """
    try:
        # Читаем первые 1024 байта для примера (можно убрать)
        content_sample = await file.read(1024)
        # Возвращаем указатель файла в начало, если нужно дальнейшее чтение
        await file.seek(0)

        print({
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content_sample),  # реальный размер требует полного чтения
            "sample_bytes": content_sample.hex()[:100]  # первые байты в hex (для демонстрации)
        })

        rspozNAT()

        return {
            "Устройство принудительного открытия": "требуется",
            "Тип конструкции": "Клапан пружинный с устройством принудительного открытия",
            "Номинальный диаметр": "100",
            "Номинальное давление": "16",
            "Тип присоединения к трубопроводу": "фланцевое",
            "Материал корпуса": "хладостойкая сталь (20ГЛ)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")