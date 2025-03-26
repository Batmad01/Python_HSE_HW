from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# Таблица юзеров
class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now().astimezone())
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)

    links = relationship("Link", back_populates="owner")


# Таблица ссылок
class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, index=True, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now().astimezone())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    clicks_count = Column(Integer, default=0)
    last_clicked_at = Column(DateTime(timezone=True), default=lambda: datetime.now().astimezone(), nullable=False)
    is_active = Column(Boolean, default=True)

    owner = relationship("User", back_populates='links')
