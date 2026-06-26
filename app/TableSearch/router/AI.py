# from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
# import json
# import re

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
        
        if user_promt:
            promt = f"{user_promt}. Шаблон - {params}"
        else:
            promt = get_promt(res_params)
        
        
        content = await convert_file_to_jpeg_content(file)
        
        if not content:
            return {"error": "Unsupported file format"}

        content.append({"type": "text", "text": promt})

        # response = await client.chat.completions.create(
        #     model=model_type,
        #     max_tokens=8000,
        #     messages=[{"role": "user", "content": content}],
        #     response_format={"type": "json_object"}
        # )
        # res = response.model_dump()
        # total_coast = res['usage']['total_cost']
        total_coast = 3.101
        # need = res['choices'][0]['message']['content']
        # parsed_need = json.loads(need)
        # parsed_need = {
        #     "Устройство принудительного открытия": "не требуется",
        #     "Сильфон": "не требуется",
        #     "Тип конструкции": "Клапан пружинный",
        #     "Номинальный диаметр": "100",
        #     "Номинальное давление": "100",
        #     "Тип присоединения к трубопроводу": "фланцевое",
        #     "Фланцевое исполнение": "с КОФ",
        #     "Тип уплотнения затвора": "металл-металл",
        #     "Материал корпуса": "20ГЛ/20ГМЛ",
        #     "По способу сброса рабочей среды ": "закрытого типа",
        #     "Упаковка": "на поддон",
        #     "Наличие КОФ": "с КОФ",
        #     "Наличие ЗИП": "ЗИП на 2 года",
        #     "Маркировка": "АМ211.100.16.3310"
        # }
        parsed_need = {
            "Устройство принудительного открытия": "не требуется",
            "Сильфон": "не требуется",
            "Тип конструкции": "Клапан пружинный",
            "Номинальный диаметр": "100",
            "Номинальное давление": "10 МПа",
            "По способу сброса рабочей среды ": "закрытого типа",
            "Упаковка": "-",
            "Наличие КОФ": "с КОФ",
            "Наличие ЗИП": "-"
        }
        
        # Сохраняем статистику
        # stat_info = await build_statistic_data(db, user_id, product_id)
        # stat_info['parameters'] = parsed_need
        # stat_info['total_coast'] = total_coast0
        
        # is_dump = await statistic_router.save_recognition(stat_info)
        fin_all = time.time()
        print(f"Распознали ОЛ за {fin_all - start_all}")
        return parsed_need
    except HTTPException:
        raise
    except Exception as e:
        print(123, str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")
