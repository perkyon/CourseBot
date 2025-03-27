import asyncio
import logging

from aiogram import Dispatcher
from aiogram.client.bot import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from yookassa import Configuration
from config import API_TOKEN
from database import init_db
from admin_handlers import register_admin_handlers
from user_handlers import register_user_handlers

from config import YOOKASSA_ACCOUNT_ID, YOOKASSA_SECRET_KEY
from yookassa import Configuration

Configuration.account_id = YOOKASSA_ACCOUNT_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY
print("In main => ", Configuration.account_id, Configuration.secret_key)  # отладочный print


async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()

    # Создаём сессию и указываем глобальный parse_mode
    session = AiohttpSession()
    session.default_parse_mode = ParseMode.HTML

    # Теперь создаём Bot с указанной сессией
    bot = Bot(token=API_TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())

    register_admin_handlers(dp)
    register_user_handlers(dp)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
