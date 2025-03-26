from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.config import DB_URL


engine = create_async_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# Асинхронная функция получения сессии базы данных
async def get_db():
    async with SessionLocal() as session:
        yield session


# Асинхронная функция инициализации базы данных
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session():
    async for s in get_db():
        yield s
