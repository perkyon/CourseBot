# main.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from yookassa import Configuration

from config import (
    API_TOKEN,
    YOOKASSA_ACCOUNT_ID,
    YOOKASSA_SECRET_KEY
)
from database import init_db
from admin_handlers import register_admin_handlers
from user_handlers import register_user_handlers

async def main():
    logging.basicConfig(level=logging.INFO)

    # Инициализация базы (создать таблицы, если не созданы)
    init_db()

    # Устанавливаем реквизиты ЮKassa
    Configuration.account_id = YOOKASSA_ACCOUNT_ID
    Configuration.secret_key = YOOKASSA_SECRET_KEY
    print("DEBUG: account_id =", Configuration.account_id)
    print("DEBUG: secret_key =", Configuration.secret_key)

    # Создаём бота и диспетчер
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем хендлеры
    register_admin_handlers(dp)
    register_user_handlers(dp)

    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
