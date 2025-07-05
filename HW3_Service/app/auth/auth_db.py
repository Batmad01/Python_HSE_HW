from collections.abc import AsyncGenerator
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import DB_URL
from app.models import User


engine = create_async_engine(DB_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Создание асинхронной сессии для работы с БД
    """
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """
    Предоставление зависимости для доступа к БД пользователей
    """
    yield SQLAlchemyUserDatabase(session, User)
