import pytest_asyncio
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from httpx import ASGITransport, AsyncClient
from typing import Callable

from app.main import app
from app.models import Base
from app.db import get_db

# from unittest.mock import AsyncMock
# from app.routers.redis_client import redis_client


pytestmark = pytest.mark.asyncio


# @pytest_asyncio.fixture
# async def mock_redis():
#     """
#     Фикстура для создания мок-объекта Redis
#     """
#     redis_mock = AsyncMock(wraps=redis_client)
#     redis_mock.get.return_value = None
#     yield redis_mock


@pytest_asyncio.fixture
async def db_session():
    """
    Фикстура для создания тестовой in-memory БД
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False})
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        async with async_session(bind=conn) as session:
            yield session
    await engine.dispose()


@pytest_asyncio.fixture()
def get_db_override(db_session: AsyncSession):
    """
    Фикстура для переопределения в приложении зависимости БД
    """
    async def override_get_db():
        yield db_session

    return override_get_db


@pytest_asyncio.fixture(autouse=True)
def app_fixture(get_db_override: Callable):
    """
    Основная фикстура приложения - подменяет БД на тестовую версию
    """
    app.dependency_overrides[get_db] = get_db_override
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(app_fixture):
    """
    Асинхронный HTTP-клиент для тестирования роутов приложения
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://tests") as ac:
        yield ac

# Выделим основные роуты
API_AUTH_REGISTER = "/auth/register"
API_AUTH_LOGIN = "/auth/jwt/login"
API_CREATE_PUBLIC = "/links/public"
API_CREATE_SHORTEN = "/links/shorten"
API_REDIRECT = "/links"
API_LINK_STATS = "/links"
API_SEARCH = "/links/search/"
API_USER_ALL = "/links/user/all"


@pytest.fixture
def user_data():
    """
    Данные для регистрации / логина тестового пользователя.
    """
    return {
        "email": "testuser@example.com",
        "password": "supersecret",
        "is_active": True,
        "is_superuser": False}


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient, user_data: dict):
    """
    Регистрация пользователя и логин,
    возвращает заголовок Authorization
    """
    # Регистрация
    r = await async_client.post(API_AUTH_REGISTER, json=user_data)
    assert r.status_code in (200, 201), r.text  # fastapi-users возвращает 200/201

    # Логин
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]}

    r_login = await async_client.post(API_AUTH_LOGIN, data=login_data)
    assert r_login.status_code == 200, r_login.text
    token = r_login.json()["access_token"]

    # Заголовок с токеном
    headers = {"Authorization": f"Bearer {token}"}
    yield headers
    await async_client.close()


# Основные тесты
async def test_root(async_client: AsyncClient):
    """
    Тестируем стартовую страницу (GET /)
    """
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "App healthy"}


async def test_public_create_and_redirect_and_stats(async_client: AsyncClient):
    """
    Тестируем публичное создание ссылки (POST /links/public),
    затем проверяем редирект (GET /links/{short_code}),
    и статистику (GET /links/{short_code}/stats)
    """
    plus_day = (datetime.now() + timedelta(days=1)).isoformat()

    # Создаём публичную ссылку
    payload = {
        "original_url": "http://example-public.com/",
        "expires_at": plus_day,
        "custom_alias": None}

    resp = await async_client.post(API_CREATE_PUBLIC, json=payload)
    assert resp.status_code == 200, resp.text
    link_data = resp.json()
    short_code = link_data["short_code"]
    assert link_data["original_url"] == "http://example-public.com/"

    # Редирект
    resp_redirect = await async_client.get(f"{API_REDIRECT}/{short_code}")
    assert resp_redirect.status_code == 307, resp_redirect.text
    assert resp_redirect.headers["Location"] == "http://example-public.com/"

    # Проверка статистики
    resp_stats = await async_client.get(f"{API_LINK_STATS}/{short_code}/stats")
    assert resp_stats.status_code == 200, resp_stats.text
    stats_data = resp_stats.json()
    assert stats_data["clicks_count"] == 1
    assert stats_data["original_url"] == "http://example-public.com/"


async def test_search_link(async_client: AsyncClient):
    """
    Тестируем поиск несозданной ссылки по оригинальному URL: GET /links/search/?original_url=...
    """
    resp_search = await async_client.get(API_SEARCH, params={"original_url": "http://search.com"})
    assert resp_search.status_code == 200
    found_data = resp_search.json()
    assert found_data is None


# async def test_auth_shortening_and_crud(async_client: AsyncClient, auth_headers: dict):
#     """
#     Проверяем закрытые эндпоинты (требуют авторизации):
#       1. POST /links/shorten
#       2. GET /links/user/all
#       3. PUT /links/{short_code}
#       4. DELETE /links/{short_code}
#     """
#     plus_day = (datetime.now().astimezone() + timedelta(days=1)).isoformat()

#     # Создаём ссылку
#     create_payload = {
#         "original_url": "http://example-1.ru",
#         "expires_at": plus_day,
#         "custom_alias": None}

#     resp_create = await async_client.post(API_CREATE_SHORTEN, json=create_payload, headers=auth_headers)
#     assert resp_create.status_code == 200, resp_create.text
#     created_link = resp_create.json()
#     short_code = created_link["short_code"]
#     assert created_link["owner_id"] is not None

#     # GET /links/user/all (все ссылки пользователя)
#     resp_user_all = await async_client.get(API_USER_ALL, headers=auth_headers)
#     assert resp_user_all.status_code == 200, resp_user_all.text
#     user_links = resp_user_all.json()
#     assert len(user_links) >= 1
#     assert any(link["short_code"] == short_code for link in user_links)

#     # PUT /links/{short_code}
#     update_payload = {
#         "original_url": "http://updated-example-1.ru",
#         "expires_at": plus_day,
#         "custom_alias": "custom-alias"}
#     resp_update = await async_client.put(f"{API_REDIRECT}/{short_code}", json=update_payload, headers=auth_headers)
#     assert resp_update.status_code == 200, resp_update.text
#     updated_link = resp_update.json()
#     assert updated_link["original_url"] == "http://updated-example-1.ru"
#     assert updated_link["short_code"] == "custom-alias"

#     # DELETE /links/{short_code}
#     resp_delete = await async_client.delete(f"{API_REDIRECT}/{updated_link['short_code']}", headers=auth_headers)
#     assert resp_delete.status_code == 200, resp_delete.text
#     deleted_link = resp_delete.json()
#     assert deleted_link["short_code"] == "custom-alias"
