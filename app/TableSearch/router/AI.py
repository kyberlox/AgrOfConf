import re
from typing import Dict, Any, Optional

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
from pydantic import BaseModel

from app.UserService.utils.auth_utils import get_user_id_by_session_id
from app.StatisticsService.utils.deps import build_statistic_data
from app.StatisticsService.router.recognition_router import get_recognition_router

from ..utils.convert_ol_file import get_params_and_values_of_product, convert_file_to_jpeg_content
from ..utils.promt_ol import VALIDATION_PROMPT, UNIFIED_PROMPT
from ..utils.prompt_storage import (
    delete_product_validation_prompt,
    get_product_validation_prompt,
    has_product_validation_prompt,
    save_product_validation_prompt,
    save_product_rules,
    get_product_rules
)

load_dotenv()
#делаю изменения
key_api = os.getenv("key_api")
model_type = os.getenv("model_type")
vseGPTurl = os.getenv("vseGPTurl")

client = AsyncOpenAI(api_key = key_api, base_url=vseGPTurl) 

router = APIRouter(prefix="/AI", tags=[""])

class Rule(BaseModel):
    name: str
    default: str

class ProductPromptPayload(BaseModel):
    payload: Optional[str] = None
    rules: Optional[list[Rule]] = None

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

        PROMT = f"""
        Из документа, который я прислал, извлеки все параметры и их значения.
        Верни результат строго в формате Markdown-таблицы с двумя колонками.

        ПРАВИЛА:

        1. Таблица: | Параметр | Значение |
        2. В значении сначала значение, потом единица измерения через запятую, если есть.
        3. Если параметр имеет несколько числовых значений с уточнениями (например, давление рабочее, настройки, расчётное) — оформи их как вложенный список с дефисом:
        | Давление (избыточное) | |
        | - Рабочее | 1.6, МПа |
        | - Настройка | 1.8, МПа |
        4. Если в строке есть выбор из вариантов (например, «да/yes нет/no», «Колпак глухой / открытый», «с пружинной нагрузкой / с грузом») — выбери тот вариант, который явно отмечен (подчёркнут, жирный, обведён, отмечен галочкой). Если отметка не видна, но один вариант вписан от руки или повторяется в соседнем тексте — используй его. Если отмечено несколько — перечисли через запятую. Если ни один не отмечен — запиши все варианты через косую черту, как в документе.
        5. Если значение не указано — пропускай строку или ставь прочерк «-».
        6. Обязательно извлеки параметры из ВСЕХ разделов: Общие сведения, Рабочие условия, Расчётные условия, Требования к конструкции, Дополнительные требования и другие, если есть. Не пропускай ни один блок.
        7. Текстовые перечисления (например, перечень документов) объединяй через запятую в одной строке.
        8. Не добавляй пояснений, только таблица.
        
        9. {user_promt}
        """
        if not user_promt:
            PROMT = UNIFIED_PROMPT
        
        content = await convert_file_to_jpeg_content(file)
        files = deepcopy(content)
        if not content:
            return {"error": "Unsupported file format"}

        content.append({"type": "text", "text": PROMT})

        response = await client.chat.completions.create(
            # model=model_type,
            model='deepseek/deepseek-v4-flash-vision-exp',
            max_tokens=8000,
            messages=[{"role": "user", "content": content}],
            # response_format={"type": "json_object"}
        )
        res = response.model_dump()
        total_coast = res['usage']['total_cost']
        # need = response.choices[0].message.content
        # total_coast = response.usage.total_cost
        need = res['choices'][0]['message']['content']
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
        # print(123, str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


@router.get("/get_product_prompt/{product_id}")
async def get_product_prompt(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Возвращает промты для продукта.

    - `validation_prompt` — свой промт продукта;
    - `unified_prompt` — общий промт распознавания (один на все продукты);
    - `rules_table` — массив дефолтных значений для параметров;
    """
    return {
        "product_id": product_id,
        "validation_prompt": get_product_validation_prompt(product_id),
        "unified_prompt": UNIFIED_PROMPT,
        "rules_table": get_product_rules(product_id)
    }


@router.post("/save_product_prompt/{product_id}")
async def save_product_prompt(
    product_id: int,
    body: ProductPromptPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Сохраняет VALIDATION-промт и RULESD_TABLE продукта (для редактирования в админке).
    Возвращает промты для продукта.
    - `validation_prompt` — свой промт продукта;
    - `rules_table` — массив дефолтных значений для параметров;
    """
    if body.payload:
        prompt = body.payload.strip()
        save_product_validation_prompt(product_id, prompt)
    if body.rules:
        save_product_rules(body.rules, product_id)
    return {
        "product_id": product_id,
        "validation_prompt": get_product_validation_prompt(product_id),
        "rules_table": get_product_rules(product_id)
    }


@router.delete("/delete_product_prompt/{product_id}")
async def delete_product_prompt(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Удаляет сохранённый VALIDATION-промт продукта (вернётся стандартный)."""
    return {"deleted": delete_product_validation_prompt(product_id)}


@router.post("/convert-ai-result")
async def convert_ai_result(
    # raw_json: dict = Body(...)
    product_id: int,
    # ol_filename: str,
    # user_promt: Optional[str] = Body(None, embed=True),
    raw_md: str = Body(...),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[int] = Depends(get_user_id_by_session_id) 
):
    try:
        #RAW_JSON: {json.dumps(raw_json, ensure_ascii=False, indent=2)} 
        params = await get_params_and_values_of_product(db, product_id)
        
        res_params = {key: value for key, value in params.items() if key not in ['Цена /шт. руб без НДС', 'Цена /шт. руб с НДС 22%']}
        
        agent_info = {
            "ФИО Заказчика": '', 
            "Телефон Заказчика": '', 
            "Email Заказчика": '', 
            "Организация Заказчика": '', 
            "Должность Заказчика": '',
            "Проектная организация": '',
            "Примечание": '',
            "Адрес Заказчика": ''
        }
        total_params = res_params | agent_info
        start_all = time.time()
        # Промт валидации — свой для продукта (если сохранён в админке), иначе стандартный.
        product_prompt = get_product_validation_prompt(product_id)
        rules_table = get_product_rules(product_id)
        messages = [
            {
                "role": "user",
                "content": f"""
                {product_prompt} (см. выше)

                RAW_MD:

                {raw_md}

                TEMPLATE_JSON:
                {json.dumps(total_params, ensure_ascii=False, indent=2)}

                RULES_TABLE:
                {rules_table}
                """
            }
        ]
        response = await client.chat.completions.create(
            # model="deepseek/deepseek-v4-flash", 
            model='deepseek/deepseek-v4-pro',
            # model='deepseek/deepseek-v4-flash-vision-exp',
            # model=model_type,
            max_tokens=4000,
            messages=messages,
            response_format={"type": "json_object"}
        )
        total_coast = response.model_dump()['usage']['total_cost']
        print(f"Total cost конвертации: {total_coast}")
        result = response.choices[0].message.content
        # need = response.choices[0].message.content
        # total_coast = response.usage.total_cost
        # # need = res['choices'][0]['message']['content']
        # parsed_need = _extract_json_from_response(result)
        
        # # Сохраняем статистику
        # stat_info = await build_statistic_data(db, user_id, product_id)
        # stat_info['parameters'] = parsed_need
        # stat_info['total_coast'] = total_coast
        # stat_info['ol_filename'] = ol_filename
        
        # is_dump = await statistic_router.save_recognition(stat_info)
        fin_all = time.time()
        print(f"Конвертировали за {fin_all - start_all}")
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки данных с thinking модели: {str(e)}")