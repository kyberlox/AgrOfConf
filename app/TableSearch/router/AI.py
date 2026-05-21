from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
import json
from typing import Dict, Any

import os
from pathlib import Path
import shutil

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

router = APIRouter(prefix="/AI", tags=[""])

client_id = "019cfb75-d657-765b-9e14-8d227ea7449d"
scope= "GIGACHAT_API_PERS"
API_KEY = "MDE5Y2ZiNzUtZDY1Ny03NjViLTllMTQtOGQyMjdlYTc0NDlkOmM4YzBlMWFlLWJkNDAtNDM0MC05YmUzLTFkOThmYzU0ZWRlMg=="

def recognize_text_from_file(file_path: str, credentials: str = None, model: str = "GigaChat-2-Pro") -> str | None:
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"Файл {file_path} не найден")

    allowed_extensions = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp')
    if file_path_obj.suffix.lower() not in allowed_extensions:
        raise ValueError(f"Неподдерживаемый формат. Допустимы: {', '.join(allowed_extensions)}")

    if credentials is None:
        credentials = API_KEY
        if not credentials:
            raise ValueError("Укажите credentials или установите переменную окружения GIGACHAT_CREDENTIALS")

    # Параметр verify_ssl_certs всё ещё нужен, чтобы клиент не пытался использовать внутренний сертификатный бандл
    client = GigaChat(
        credentials=credentials,
        verify_ssl_certs=False,
        model=model,
        timeout=600
    )

    try:
        with open(file_path_obj, "rb") as f:
            uploaded_file = client.upload_file(f, purpose="general")
        file_id = uploaded_file.id_
        print(f"Файл успешно загружен. ID: {file_id}")

        messages = Messages(
            role=MessagesRole.USER,
            content="Распознай и выведи весь текст, который содержится в этом файле. "
                    "Выведи только распознанный текст, без каких-либо дополнительных комментариев.",
            attachments=[file_id]
        )
        chat = Chat(messages=messages)
        response = client.chat("ты умеешь распознавать документы?")#messages)#, model=model)
        if response and response.choices:
            return response.choices[0].message.content
        else:
            return None
    except Exception as e:
        print(f"Ошибка обработки: {e}")
        raise

# print(recognize_text_from_file(file_path))

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

        file_path = f"../uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(recognize_text_from_file(file_path))

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