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
from fastapi import Request, HTTPException, status
import os
from dotenv import load_dotenv

from ..utils.convert_ol_file import get_params_and_values_of_product, convert_file_to_jpeg_content
from ..utils.promt_ol import get_promt

load_dotenv()
#делаю изменения
key_api = os.getenv("key_api")
model_type = os.getenv("model_type")
vseGPTurl = os.getenv("vseGPTurl")

client = AsyncOpenAI(api_key = key_api, base_url=vseGPTurl) 

router = APIRouter(prefix="/AI", tags=[""])

# client_id = "019cfb75-d657-765b-9e14-8d227ea7449d"
# scope= "GIGACHAT_API_PERS"
# API_KEY = "MDE5Y2ZiNzUtZDY1Ny03NjViLTllMTQtOGQyMjdlYTc0NDlkOmM4YzBlMWFlLWJkNDAtNDM0MC05YmUzLTFkOThmYzU0ZWRlMg=="


@router.post("/upload_OL")
async def upload_OL(
    product_id: int, 
    user_promt: Optional[str] = Body(),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    try:
        import time 
        start_all = time.time()
        params = await get_params_and_values_of_product(db, product_id)
        fin_params = time.time()
        print(f"Нашли параметры за {fin_params - start_all}")
        res_params = {key: value for key, value in params.items() if key not in ['Цена /шт. руб без НДС', 'Цена /шт. руб с НДС 22%']}
        
        if user_promt:
            promt = f"{user_promt}. Шаблон - {params}"
        else:
            promt = get_promt(res_params)
        fin_promt = time.time()
        print(f"Собрали промт за {fin_promt - fin_params}")
        content = await convert_file_to_jpeg_content(file)
        fin_content = time.time()
        print(f"Собрали контент за {fin_content - fin_promt}")
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
        fin_response = time.time()
        print(f"Получили результат за {fin_response - fin_content}")
        need = res['choices'][0]['message']['content']
        parsed_need = json.loads(need)
        fin_all = time.time()
        print(f"Собрали все за {fin_all - start_all}")
        return parsed_need
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")
