import re
from typing import Dict, Any, Optional

# import os
# from pathlib import Path
# import shutil

# from gigachat import GigaChat
# from gigachat.models import Chat, Messages, MessagesRole
from sqlalchemy.ext.asyncio import AsyncSession
from app.TablePakage.model.database import get_db
import requests
import json
import base64
import openai
from openai import OpenAI
from openai import AsyncOpenAI
from fastapi import APIRouter, Depends, Body, Response, Cookie, Request
from fastapi.responses import FileResponse
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import time
from datetime import datetime
from fastapi import Request, HTTPException, status
import os
from dotenv import load_dotenv

from app.UserService.utils.auth_utils import get_user_id_by_session_id
from app.StatisticsService.utils.deps import build_statistic_data
from app.StatisticsService.router.recognition_router import get_recognition_router

from ..utils.convert_ol_file import get_params_and_values_of_product, convert_file_to_jpeg_content
from ..utils.promt_ol import get_promt

load_dotenv()
#делаю изменения
key_api = os.getenv("key_api")
model_type = os.getenv("model_type")
vseGPTurl = os.getenv("vseGPTurl")

client = AsyncOpenAI(api_key = key_api, base_url=vseGPTurl) 

router = APIRouter(prefix="/AI", tags=[""])


def _extract_json_from_response(text: str) -> dict:
    """Извлекает JSON из ответа нейросети.
    Устойчив к markdown-блокам ```json ... ``` и лишнему тексту после JSON.
    """
    raw = text.strip()
    print(f"[DEBUG] Ответ нейросети (первые 500 символов): {raw[:500]}")

    # 1. Ищем JSON в markdown-блоке ```json ... ```
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()

    # 2. Ищем крайние фигурные скобки и пробуем спарсить
    brace_start = raw.find('{')
    brace_end = raw.rfind('}')
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        candidate = raw[brace_start:brace_end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 3. Если не нашли { — возможно ответ в другом формате, пробуем весь текст
    raise ValueError(
        f"Не удалось извлечь JSON из ответа нейросети. "
        f"Ответ (первые 500 символов): {raw[:500]}"
    )


@router.post("/upload_OL")
async def upload_OL(
    product_id: int,
    user_promt: Optional[str] = Body(None, embed=True),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    statistic_router = Depends(get_recognition_router),
    user_id: Optional[int] = Depends(get_user_id_by_session_id)
) -> Dict[str, Any]:
    
    try:
        start_all = time.time()
        params = await get_params_and_values_of_product(db, product_id)
        
        res_params = {key: value for key, value in params.items() if key not in ['Цена /шт. руб без НДС', 'Цена /шт. руб с НДС 22%']}
        print(res_params)
        agent_info = {
            "Имя заказчика": '', 
            "Телефон заказчика": '',
            "Email заказчика": '',
            "Организация заказчика": ''
        }
        total_params = res_params | agent_info
        if user_promt:
            promt = f"{user_promt}. Шаблон - {total_params}"
        else:
            promt = get_promt(total_params)
        
        
        content = await convert_file_to_jpeg_content(file)
        
        if not content:
            return {"error": "Unsupported file format"}

        content.append({"type": "text", "text": promt})

        response = await client.chat.completions.create(
            model=model_type,
            max_tokens=8000,
            messages=[{"role": "user", "content": content}],
            response_format={"type": "json_object"}
        )
        res = response.model_dump()
        total_coast = res['usage']['total_cost']
        need = res['choices'][0]['message']['content']
        parsed_need = _extract_json_from_response(need)
        
        # Сохраняем статистику
        stat_info = await build_statistic_data(db, user_id, product_id)
        stat_info['parameters'] = parsed_need
        stat_info['total_coast'] = total_coast
        
        is_dump = await statistic_router.save_recognition(stat_info)
        fin_all = time.time()
        print(f"Распознали ОЛ за {fin_all - start_all}")
        return parsed_need
    except HTTPException:
        raise
    except Exception as e:
        print(123, str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")
