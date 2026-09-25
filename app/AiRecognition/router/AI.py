import hashlib
import json
import os
import re
import time
from copy import deepcopy
from typing import Any, Dict, List, Optional
import httpx
import openai
from dotenv import load_dotenv
from fastapi import APIRouter, Body, Depends, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.StatisticsService.router.recognition_router import get_recognition_router
from app.TablePakage.model.database import get_db
from app.UserService.utils.auth_utils import get_user_id_by_session_id

from ..utils.convert_ol_file import (
    convert_file_to_jpeg_content,
    convert_file_to_pages,
    get_params_and_values_of_product,
)
from ..utils.coord_mapper import (
    build_positions,
    normalize_positions_percent,
    positions_to_dict,
)
from ..utils.ocr_engine import build_transcript, is_ocr_available, get_ocr_engine
from ..utils.promt_ol import OCR_PARSING_PROMPT, UNIFIED_PROMPT, VALIDATION_PROMPT
from ..utils.prompt_storage import (
    delete_product_validation_prompt,
    get_product_rules,
    get_product_validation_prompt,
    has_product_validation_prompt,
    save_product_rules,
    save_product_validation_prompt,
)

load_dotenv()

key_api = os.getenv("key_api")
model_type = os.getenv("model_type")
vseGPTurl = os.getenv("vseGPTurl")

client = AsyncOpenAI(api_key=key_api, base_url=vseGPTurl)

router = APIRouter(prefix="/AI", tags=["RAG"])


class Rule(BaseModel):
    name: str
    default: str


class ProductPromptPayload(BaseModel):
    payload: Optional[str] = None
    rules: Optional[list[Rule]] = None


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

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


def _hybrid_mode_enabled() -> bool:
    """Флаг переключения между гибридом (OCR+LLM) и vision-фолбэком."""
    return os.getenv("OCR_HYBRID", "0") not in {"0", "false", "False"}


def _file_cache_key(file: UploadFile) -> str:
    """Хеш байтов файла для кэширования OCR."""
    # Не читаем файл повторно — вызывается до чтения
    return ""


async def _run_llm_text_only(prompt_text: str) -> dict:
    """Текст-only вызов LLM (дешевле и быстрее vision)."""
    response = await client.chat.completions.create(
        model='deepseek/deepseek-v4-pro',
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt_text}],
        response_format={"type": "json_object"},
    )
    res = response.model_dump()
    need = res['choices'][0]['message']['content']
    total_coast = res['usage']['total_cost']
    return {"parsed": _extract_json_from_response(need), "total_coast": total_coast}


# async def _run_llm_vision(content: list) -> dict:
#     """Vision-вызов LLM (фолбэк для рукописных документов)."""
#     response = await client.chat.completions.create(
#         model='deepseek/deepseek-v4-flash-vision-exp',
#         max_tokens=8000,
#         messages=[{"role": "user", "content": content}],
#         timeout=httpx.Timeout(60.0, connect=10.0)
#     )
#     res = response.model_dump()
#     need = res['choices'][0]['message']['content']
#     total_coast = res['usage']['total_cost']
#     # return {"parsed": _extract_json_from_response(need), "total_coast": total_coast}
#     return {"parsed": need, "total_coast": total_coast}
async def _run_llm_vision(content: list, retries: int = 3) -> dict:
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            response = await client.chat.completions.create(
                model='deepseek/deepseek-v4-flash-vision-exp',
                max_tokens=8000,
                messages=[{"role": "user", "content": content}],
            )
            res = response.model_dump()
            need = res['choices'][0]['message']['content']
            total_coast = res['usage']['total_cost']
            return {"parsed": need, "total_coast": total_coast}
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
            last_exc = e
            if attempt == retries:
                break
            wait = min(2 ** attempt, 10)
            await asyncio.sleep(wait)
    raise last_exc

# ---------------------------------------------------------------------------
# Эндпоинты
# ---------------------------------------------------------------------------

@router.post("/upload_OL")
async def upload_OL(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[int] = Depends(get_user_id_by_session_id),
):
    from copy import deepcopy
    try:
        start_all = time.time()
        hybrid = _hybrid_mode_enabled() and is_ocr_available()
        print(f"[AiRecognition] OCR_HYBRID={_hybrid_mode_enabled()}, OCR available={is_ocr_available()} → {'hybrid' if hybrid else 'vision'}")

        # 1. Конвертация файла → JPEG-страницы с размерами
        pages = await convert_file_to_pages(file)
        if not pages:
            return {"error": "Unsupported file format"}
        files = [p.item for p in pages]
        # Размеры страниц (px) — для пересчёта координат в проценты:
        # {index_страницы: (width, height)}
        page_sizes = {p.index: (p.width, p.height) for p in pages}

        if hybrid:
            # ---- ГИБРИД: локальный OCR + текст-only LLM -------------------
            # Весь блок обёрнут в try/except: любая ошибка OCR (включая
            # несовместимость входных данных, падение движка) НЕ роняет
            # контейнер, а переключает обработку на vision-фолбэк.
            try:
                ocr_start = time.time()

                # 2. OCR всех страниц (боксы слов) + транскрипт
                engine = get_ocr_engine()
                pages_jpeg = [(p.index, p.jpeg_bytes) for p in pages[: engine.max_pages]]
                words_by_page = await engine.ocr_pages(pages_jpeg)
                transcript = await engine.build_transcript(words_by_page)
                ocr_time = time.time() - ocr_start
                print(f"[AiRecognition] OCR {len(pages_jpeg)} стр. за {ocr_time:.2f}s")

                if not transcript.strip():
                    # OCR ничего не распознал — аварийный фолбэк на vision
                    print("[AiRecognition] OCR пустой транскрипт → vision фолбэк")
                    hybrid = False
            except Exception as e:
                print(f"[AiRecognition] Ошибка OCR: {e} → vision фолбэк")
                try:
                    engine.mark_broken()
                except Exception:
                    pass
                hybrid = False

        if not hybrid:
            # ---- VISION ФОЛБЭК (старый путь) ------------------------------
            content = deepcopy(files)
            
            PROMT = UNIFIED_PROMPT
            content.append({"type": "text", "text": PROMT})

            llm_result = await _run_llm_vision(content)
            parsed_need = llm_result["parsed"]
            total_coast = llm_result["total_coast"]
            # УБРАЛИ КООРДИНАТЫ
            # data = parsed_need.get("data", "")
            # positions = parsed_need.get("positions", [])
            # Vision-модель тоже возвращает пиксели в своём масштабе →
            # переводим в проценты от размера страницы для фронтенда.
            # positions = normalize_positions_percent(positions, page_sizes)
        else:
            # ---- ПРОДОЛЖЕНИЕ ГИБРИДА --------------------------------------
            llm_start = time.time()
            prompt_text = f"{OCR_PARSING_PROMPT}\n\nТРАНСКРИПТ ДОКУМЕНТА:\n\n{transcript}"
            llm_result = await _run_llm_text_only(prompt_text)
            parsed_need = llm_result["parsed"]
            total_coast = llm_result["total_coast"]
            data = parsed_need.get("data", "")
            llm_time = time.time() - llm_start
            print(f"[AiRecognition] LLM текст-only за {llm_time:.2f}s")

            # 3. Сопоставление строк таблицы ↔ боксов OCR
            align_start = time.time()
            lines_by_page = {}
            for idx, page_words in enumerate(words_by_page):
                if page_words:
                    lines_by_page.setdefault(page_words[0].page_index, []).extend(
                        engine.cluster_into_lines(page_words)
                    )
            positions = positions_to_dict(
                build_positions(
                    data,
                    words_by_page,
                    lines_by_page,
                    log_reasons=True,
                )
            )
            # Пиксели OCR (300 DPI) → проценты от размера страницы:
            # масштабируются на любой CSS-размер картинки.
            positions = normalize_positions_percent(positions, page_sizes)
            align_time = time.time() - align_start
            print(f"[AiRecognition] Align {len(positions)} позиций за {align_time:.2f}s")

        fin_all = time.time()
        print(f"Распознали ОЛ за {fin_all - start_all:.2f}s, Цена: {total_coast}")

        # return {"markdown": data, "positions": positions, "file": files}
        return {"markdown": parsed_need, "file": files}
    except HTTPException:
        raise
    except Exception as e:
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
        "rules_table": get_product_rules(product_id),
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
        "rules_table": get_product_rules(product_id),
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
    product_id: int,
    raw_md: str = Body(...),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[int] = Depends(get_user_id_by_session_id),
):
    try:
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
            "Адрес Заказчика": '',
        }
        total_params = res_params | agent_info
        start_all = time.time()
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
                """,
            }
        ]
        response = await client.chat.completions.create(
            model='deepseek/deepseek-v4-pro',
            max_tokens=4000,
            messages=messages,
            response_format={"type": "json_object"},
        )
        total_coast = response.model_dump()['usage']['total_cost']
        print(f"Total cost конвертации: {total_coast}")
        result = response.choices[0].message.content
        fin_all = time.time()
        print(f"Конвертировали за {fin_all - start_all:.2f}s")
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки данных с thinking модели: {str(e)}")