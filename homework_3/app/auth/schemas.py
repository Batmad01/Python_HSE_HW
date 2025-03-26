import uuid
from fastapi_users import schemas
from pydantic import BaseModel, HttpUrl, ConfigDict
import datetime
from typing import Optional


# Users
class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


# Links
# Создание новой ссылки
class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime.datetime] = None


# Ответ API на создание ссылки
class LinkResponse(BaseModel):
    id: int
    original_url: HttpUrl
    short_code: str
    created_at: datetime.datetime
    expires_at: datetime.datetime
    clicks_count: int
    last_clicked_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True


# Модель ответа для статуса приложения "/"
class StatusResponse(BaseModel):
    status: str
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "App healthy"}]})
