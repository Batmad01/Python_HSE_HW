import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import setup_handlers
from aiogram.fsm.storage.memory import MemoryStorage

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
setup_handlers(dp)


# Настройка команд
async def set_bot_commands(bot: Bot):
    commands = [
        {"command": "start", "description": "Начать работу с ботом"},
        {"command": "set_profile", "description": "Настроить профиль"},
        {"command": "show_profile", "description": "Просмотр текущего профиля"},
        {"command": "log_water", "description": "Записать количество выпитой воды"},
        {"command": "log_food", "description": "Записать количество ккал"},
        {"command": "log_workout", "description": "Записать количество сожённых калорий на тренировке"},
        {"command": "check_progress", "description": "Отобразить прогресс по воде и калориям"}
    ]
    await bot.set_my_commands(commands)


# Основная функция запуска бота
async def main():
    # Установка команд бота
    await set_bot_commands(bot)

    # Запуск бота
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
