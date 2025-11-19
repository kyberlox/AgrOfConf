from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.SaveOfConf.router import product_router

app = FastAPI(title="SaveOfConf API", version="1.0.0")

# Подключаем статические файлы
app.mount("/api/files", StaticFiles(directory="./static"), name="static")

# Подключаем роутеры
app.include_router(product_router, prefix="/api")

@app.get("/")
async def read_root():
    return {"message": "Welcome to SaveOfConf API"}
