from fastapi import FastAPI
import asyncio
from contextlib import asynccontextmanager

from app.routers import links, user_auth
from app.db import init_db
from app.utils import delete_old_links
from app.auth.schemas import StatusResponse


# Создание БД при запуске и фоновой задачи удаления устаревших ссылок
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(delete_old_links())
    yield
    task.cancel()

# Инициализация приложения
app = FastAPI(title="URL Shortener",
              docs_url="/api/docs",
              openapi_url="/api/docs.json")

# Подключаем роутеры
app.include_router(user_auth.router)
app.include_router(links.router)


# Статус приложения
@app.get("/", response_model=StatusResponse, summary="Root",
         description="Информация о статусе сервиса")
async def root():
    """
    Проверки статуса приложения
    Возвращает JSON со статусом работы сервиса
    """
    return StatusResponse(status="App healthy")
