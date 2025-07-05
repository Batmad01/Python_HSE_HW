import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select
from app.models import Base, Link
from app.utils import generate_short_code


# Фикстура для движка БД
@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


# Фикстура для сессии БД
@pytest_asyncio.fixture
async def session(engine):
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


# Тестирование
@pytest.mark.asyncio
async def test_code_gen(session: AsyncSession):
    # Тест генерации нового кода
    short_code = generate_short_code()
    assert len(short_code) == 6

    # Проверка отсутствия кода в бд
    result = await session.execute(select(Link).where(Link.short_code == short_code))
    assert result.scalar() is None
