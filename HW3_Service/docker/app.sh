#!/bin/bash

# Миграция
alembic upgrade head

# Запуск приложения
uvicorn app.main:app --host 0.0.0.0 --port 8000