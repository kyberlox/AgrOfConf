from fastapi import FastAPI, Depends, Request, Response, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import json
from typing import List
#from .TablePakage.model.product import Product
# from .FormulaPakage.model import *

from .TablePakage.router.products import router as products_router
from .TablePakage.router.parameters import router as parameters_router
from .TablePakage.router.tables import router as tables_router
from .TablePakage.router.parameter_values import router as parameter_values_router
from .TableSearch.router.module_search import router as module_search_router
from .TableSearch.router.module_search_pandas import router as module_search_router_pandas
from .TableSearch.router.AI import router as AI_router
from .TablePakage.router.tkp_generation import router as tkp_generation

from .TablePakage.model.database import create_tables
import app.logging_config
from .TablePakage.model.database import create_tables

from .UserService.services.redis_service import RedisStorage
from .UserService.utils.auth_utils import validate_users_sessions, create_session, refresh_session_id
from .UserService.router.users_router import router as users_router
from .UserService.router.auth_router import router as auth_router
from .UserService.router.roots_router import router as roots_router

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dotenv import load_dotenv

load_dotenv()



app = FastAPI(
    title="SaveOfConf API",
    version="1.0.0",
    docs_url="/api/docs", #None
    openapi_url="/api/openapi.json"
)



# # Настройка CORS
origins = ["http://localhost:5173", "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Открытые эндпоинты
open_links = ["/api/docs", "/api/openapi.json"]

redis_storage = RedisStorage()

# @app.middleware("http")
# async def session_middleware(request: Request, call_next):
#     try:
#         ttl_refresh_threshold = 300
#         path = request.url.path
#         # Пропускаем открытые эндпоинты
#         if path in open_links:
#             return await call_next(request)

#         # Получаем session_id из cookie
#         session_id = request.cookies.get("session_id")
#         if not session_id:
#             raise HTTPException(status_code=401, detail="Missing session cookie")

#         # Проверяем существование и TTL сессии в Redis
#         user_id = redis_storage.get_session(session_id)
#         if user_id is None:
#             raise HTTPException(status_code=401, detail="Invalid or expired session")

#         ttl = redis_storage.get_ttl(session_id)
#         # Если ключ есть, но TTL == -1 (нет истечения) – не нужно обновлять
#         # Если TTL < 0 (ошибка) – считаем, что сессия не валидна
#         if ttl < 0 and ttl != -1:
#             raise HTTPException(status_code=401, detail="Session error")

#         # Обновление сессии, если осталось меньше порога
#         if ttl > 0 and ttl <= ttl_refresh_threshold:
#             # Вызываем внешнее API для получения нового session_id
#             refresh_data = await refresh_session_id(session_id)
#             if refresh_data['status'] != "success":
#                 # Не удалось обновить – можно либо вернуть 401, либо продолжить с той же сессией
#                 # По логике – лучше вернуть 401, так как сессия скоро истечёт и токен не продлён
#                 raise HTTPException(status_code=401, detail="Session refresh failed")

#             new_session_id = refresh_data["session_id"]

#             # Удаляем все старые сессии пользователя
#             await validate_users_sessions(user_id)

#             # Создаём новую сессию
#             await create_session(new_session_id, user_id)  # create_session асинхронная

#             # Устанавливаем новую cookie
#             resp = await call_next(request)
#             resp.set_cookie(
#                 key="session_id",
#                 value=new_session_id,
#                 samesite="lax"
#             )
#             return resp

#         # Если TTL > порога – просто продлеваем время жизни (скользящая сессия)
#         if ttl > 0:
#             # Продлеваем на стандартное время (например, 1 час)
#             redis_storage.expire_session(session_id, int(redis_storage.session_ttl.total_seconds()))

#         # Обычный случай – вызываем следующий обработчик
#         response = await call_next(request)
#         return response
#     except HTTPException as e:
#         return JSONResponse(status_code=e.status_code, content={"detail": e.detail})


# Создаём таблицы при старте приложения
@app.on_event("startup")
async def startup_event():
    await create_tables()


# Подключаем статические файлы (для изображений)
# app.mount("/static", StaticFiles(directory="app/products/static"), name="static")
app.mount("/api/files", StaticFiles(directory="./static"), name="files")

# Подключаем роутеры
app.include_router(products_router, prefix="/api")
app.include_router(parameters_router, prefix="/api")
app.include_router(tables_router, prefix="/api")
app.include_router(parameter_values_router, prefix="/api")
app.include_router(module_search_router, prefix="/api")
app.include_router(module_search_router_pandas, prefix="/api")
app.include_router(AI_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(roots_router, prefix="/api")
app.include_router(tkp_generation, prefix="/api")

# app.include_router(calculated_router, prefix="/api")
# app.include_router(user_input_router, prefix="/api")
# app.include_router(condition_router, prefix="/api")
# app.include_router(selected_file_router, prefix="/api")
# app.include_router(fields_of_view_router, prefix="/api")
# app.include_router(constants_router, prefix="/api")

# app.include_router(code_router, prefix="/api")



# app.include_router(formulas_router, prefix="/api")



@app.get("/")
async def read_root():
    return {"message": "Welcome to App for API"}


# В app/main.py
@app.get("/health")
async def health_check():
    return {"status": "ok"}
