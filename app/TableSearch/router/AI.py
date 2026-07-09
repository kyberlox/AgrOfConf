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
from ..utils.promt_ol import get_promt, VALIDATION_PROMPT, UNIFIED_PROMPT

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
    # product_id: int,
    user_promt: Optional[str] = Body(None, embed=True),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    statistic_router = Depends(get_recognition_router),
    user_id: Optional[int] = Depends(get_user_id_by_session_id)
): # -> Dict[str, Any]
    from copy import deepcopy
    try:
        start_all = time.time()
        # params = await get_params_and_values_of_product(db, product_id)
        
        # res_params = {key: value for key, value in params.items() if key not in ['Цена /шт. руб без НДС', 'Цена /шт. руб с НДС 22%']}
        
        # agent_info = {
        #     "Имя заказчика": '', 
        #     "Телефон заказчика": '',
        #     "Email заказчика": '',
        #     "Организация заказчика": ''
        # }
        # total_params = res_params | agent_info
        PROMT = f"""
        Из документа, который я прислал, извлеки все параметры и их значения.
        Верни результат строго в формате Markdown-таблицы с двумя колонками.

        ПРАВИЛА ФОРМИРОВАНИЯ MARKDOWN:

        1. Используй таблицу с колонками: | Параметр | Значение |
        
        2. В колонке "Значение" запиши сначала значение параметра, 
        а если есть размерность — добавь её через запятую после значения.
        
        Примеры:
        | Номинальный диаметр | 100, мм |
        | Тип присоединения к трубопроводу | фланцевое |
        | Давление (избыточное) | 1.6, МПа |
        
        3. {user_promt}
        В ответе пришли ТОЛЬКО Markdown-таблицу, без пояснений.
        """
        if not user_promt:
            PROMT = UNIFIED_PROMPT
        
        content = await convert_file_to_jpeg_content(file)
        files = deepcopy(content)
        if not content:
            return {"error": "Unsupported file format"}

        content.append({"type": "text", "text": PROMT})

        response = await client.chat.completions.create(
            model=model_type,
            max_tokens=8000,
            messages=[{"role": "user", "content": content}],
            # response_format={"type": "json_object"}
        )
        # res = response.model_dump()
        # total_coast = res['usage']['total_cost']
        need = response.choices[0].message.content
        total_coast = response.usage.total_cost
        # need = res['choices'][0]['message']['content']
        # parsed_need = _extract_json_from_response(need)
        
        # Сохраняем статистику
        # stat_info = await build_statistic_data(db, user_id, product_id)
        # stat_info['parameters'] = parsed_need
        # stat_info['total_coast'] = total_coast
        
        # is_dump = await statistic_router.save_recognition(stat_info)
        fin_all = time.time()
        print(f"Распознали ОЛ за {fin_all - start_all}, Цена: {total_coast}")
        return {"markdown": need, "file": files}
    except HTTPException:
        raise
    except Exception as e:
        print(123, str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


@router.post("/convert-ai-result")
async def convert_ai_result(
    # raw_json: dict = Body(...)
    product_id: int,
    raw_md: str = Body(...),
    db: AsyncSession = Depends(get_db) 
):
    try:
        #RAW_JSON: {json.dumps(raw_json, ensure_ascii=False, indent=2)} 
        params = await get_params_and_values_of_product(db, product_id)
        
        res_params = {key: value for key, value in params.items() if key not in ['Цена /шт. руб без НДС', 'Цена /шт. руб с НДС 22%']}
        
        agent_info = {
            "Имя заказчика": '', 
            "Телефон заказчика": '',
            "Email заказчика": '',
            "Организация заказчика": ''
        }
        total_params = res_params | agent_info
        start_all = time.time()
        messages = [
        {
            "role": "user",
            "content": f"""
            {VALIDATION_PROMPT} (см. выше)

            RAW_MD:

            {raw_md}

            TEMPLATE_JSON:
            {json.dumps(total_params, ensure_ascii=False, indent=2)}

            RULES:
            - Сопоставь ключи из Markdown с TEMPLATE_JSON по смыслу
            - Выбери только допустимые значения из TEMPLATE_JSON
            - Если точного совпадения нет — выбери ближайшее
            - Пропусти параметры, которых нет в TEMPLATE_JSON
            - Верни JSON в формате: {{"параметр": "значение"}}
            - Размерность НЕ включай в результат
            """
            }
        ]
        response = await client.chat.completions.create(
            model="deepseek/deepseek-v4-flash", 
            max_tokens=4000,
            messages=messages,
            response_format={"type": "json_object"}
        )
        total_coast = response.model_dump()['usage']['total_cost']
        print(f"Total cost конвертации: {total_coast}")
        result = response.choices[0].message.content
        
        fin_all = time.time()
        print(f"Конвертировали за {fin_all - start_all}")
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки данных с vision модели: {str(e)}")