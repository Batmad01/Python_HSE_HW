import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Чтение токенов из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
TEMP_TOKEN = os.getenv("TEMP_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

if not TEMP_TOKEN:
    raise ValueError("Переменная окружения TEMP_TOKEN не установлена!")
