import secrets
import string
from datetime import datetime, timezone
import asyncio
from sqlalchemy import select

from app.db import SessionLocal
from app.routers.redis_client import redis_client
from app.models import Link


def generate_short_code(length: int = 6) -> str:
    """
    Генерация случайного короткого кода
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def delete_old_links():
    """
    Фоновая задача удаления устаревших ссылок
    """
    while True:
        async with SessionLocal() as session:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            expired_links = await session.execute(
                select(Link).where(Link.expires_at.isnot(None), Link.expires_at <= now))
            expired_links = expired_links.scalars().all()

            # удаляем из основной таблицы и из кэша
            for link in expired_links:
                await session.delete(link)
                redis_client.delete(link.short_code)
                redis_client.delete(f"stats:{link.short_code}")
                redis_client.delete(f"search:{link.original_url}")

            await session.commit()

        await asyncio.sleep(30)
