from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from fastapi.responses import RedirectResponse
import json

from app.auth.users import current_active_user
from app.db import get_db
from app import models, utils
from app.auth import schemas
from app.routers.redis_client import redis_client

# Основной роутер
router = APIRouter(prefix="/links", tags=['Links'])


@router.post("/shorten", response_model=schemas.LinkResponse)
async def create_link(
    link_data: schemas.LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(current_active_user),
):
    """
    Создание короткого кода ссылки на основе оригинального url
    """
    # Если алиас задан - проверяем уникальность
    if link_data.custom_alias:
        stmt = select(models.Link).where(models.Link.short_code == link_data.custom_alias)
        result = await db.execute(stmt)
        exists = result.scalar_one_or_none()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Алиас уже существует")
        short_code = str(link_data.custom_alias)
    else:
        short_code = str(utils.generate_short_code())

    # Если алиаса нет - создаём новую ссылку
    new_link = models.Link(
        original_url=str(link_data.original_url),
        short_code=str(short_code),
        owner_id=current_user.id if current_user else None,
        expires_at=link_data.expires_at.astimezone(),
        created_at=datetime.now().astimezone(),
        last_clicked_at=datetime.now().astimezone(),
        clicks_count=0)

    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return new_link


@router.get("/{short_code}")
async def redirect_link(short_code: str, db: AsyncSession = Depends(get_db)):
    """
    Редирект с короткого кода ссылки на оригинальный url
    """
    stmt = select(models.Link).where(models.Link.short_code == short_code)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена")

    # Проверяем expires_at
    if link.expires_at and link.expires_at < datetime.now().astimezone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка истекла")

    # Обновляем статистику
    link.clicks_count += 1
    link.last_clicked_at = datetime.now().astimezone()
    await db.commit()
    return RedirectResponse(link.original_url)


@router.get("/{short_code}/stats", response_model=schemas.LinkResponse)
async def get_link_stats(short_code: str, db: AsyncSession = Depends(get_db)):
    """
    Получение статистики о ссылке по её короткому коду
    """
    # Проверка кэширования в redis
    cache_key = f"stats:{short_code}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Если нет кэша - делаем запрос в БД
    stmt = select(models.Link).where(models.Link.short_code == short_code)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена")

    # Преобразуем результат через Pydantic-схему и сохраняем данные в Redis
    link_data = schemas.LinkResponse.model_validate(link).model_dump()
    redis_client.setex(cache_key, 600, json.dumps(link_data, default=str))

    return link


@router.delete("/{short_code}", response_model=schemas.LinkResponse)
async def delete_link(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(current_active_user),
):
    """
    Удаление ссылки по её короткому коду
    """
    stmt = select(models.Link).where(models.Link.short_code == short_code)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена")

    if link.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Недостаточно прав для удаления ссылки")

    await db.delete(link)
    await db.commit()
    redis_client.delete(short_code)
    redis_client.delete(f"stats:{short_code}")

    return link


@router.put("/{short_code}", response_model=schemas.LinkResponse)
async def update_link(
    short_code: str,
    update_data: schemas.LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(current_active_user),
):
    """
    Обновление данных ссылки
    """
    stmt = select(models.Link).where(models.Link.short_code == short_code)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена")

    if link.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Недостаточно прав для обновления ссылки")

    # Очистка кэша перед обновлением ссылки
    redis_client.delete(short_code)
    redis_client.delete(f"stats:{short_code}")

    # Проверка alias
    if update_data.custom_alias and update_data.custom_alias != link.short_code:
        stmt_alias = select(models.Link).where(models.Link.short_code == update_data.custom_alias)
        alias_result = await db.execute(stmt_alias)
        alias_exists = alias_result.scalar_one_or_none()
        if alias_exists:
            raise HTTPException(status_code=400, detail="Алиас уже используется")
        link.short_code = str(update_data.custom_alias)

    link.original_url = str(update_data.original_url)
    link.expires_at = update_data.expires_at

    await db.commit()
    await db.refresh(link)
    return link


@router.get("/search/")
async def search_link(original_url: str, db: AsyncSession = Depends(get_db)):
    """
    Поиск короткой ссылки по оригинальному url
    """
    # Проверка кэширования
    cache_key = f"search:{original_url}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Если нет кэша - запрос в БД
    stmt = select(models.Link).where(models.Link.original_url == original_url)
    result = await db.execute(stmt)

    # Если нашли ссылку
    link = result.scalar_one_or_none()
    if link:
        link_data = schemas.LinkResponse.model_validate(link).model_dump()
        redis_client.setex(cache_key, 600, json.dumps(link_data, default=str))
        return link_data
    return None


@router.post("/public", response_model=schemas.LinkResponse)
async def shorten_url_public(link_data: schemas.LinkCreate,
                             db: AsyncSession = Depends(get_db)):
    """
    Создание короткой ссылки для незарегистрированных пользователей
    """
    # Если алиас задан - проверяем уникальность
    if link_data.custom_alias:
        stmt = select(models.Link).where(models.Link.short_code == link_data.custom_alias)
        result = await db.execute(stmt)
        exists = result.scalar_one_or_none()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Алиас уже существует")
        short_code = str(link_data.custom_alias)
    else:
        short_code = str(utils.generate_short_code())

    # Если алиаса нет - создаём новую ссылку
    new_link = models.Link(
        original_url=str(link_data.original_url),
        short_code=str(short_code),
        expires_at=link_data.expires_at.astimezone(),
        created_at=datetime.now().astimezone(),
        last_clicked_at=datetime.now().astimezone(),
        clicks_count=0)

    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return new_link


@router.get("/user/all", response_model=List[schemas.LinkResponse])
async def get_user_links(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(current_active_user)
):
    """
    Получение списка всех ссылок пользователя с их статусом
    """
    stmt = select(models.Link).where(models.Link.owner_id == current_user.id)
    result = await db.execute(stmt)
    links = result.scalars().all()
    return links
