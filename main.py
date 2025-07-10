import asyncio
import asyncpg
import logging
import sys
import datetime  # Не забудьте импортировать datetime
from aiogram.fsm.storage.memory import MemoryStorage
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from app.handlers import router
from app.admin import admin
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from datetime import datetime
from database.queries import *
from database.create import *
from database.connection import connection


load_dotenv()


# Вызов функции
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("bot.log"),  # Имя файла для логов
            logging.StreamHandler()  # Вывод в консоль
        ]
    )
    logger = logging.getLogger(__name__)

async def update_last_activity(user_id):
    conn = await connection()
    current_time = datetime.datetime.now().isoformat()
    await conn.execute(UPDATE_LAST_ACTIVITY, current_time, user_id)
    await conn.close()

# Настройка логирования


async def main() -> None:
    # Подключение к базе данных PostgreSQL
    conn = await connection()
    #cursor = conn.cursor()

    # Создание таблицы профилей, если она не существует
    try:
        await conn.execute(CREATE_PROFILES)
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка при создании таблиц: {e}")

    # Создание таблицы для хранения лайков, если она не существует
    try:
        await conn.execute(CREATE_LIKES)
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка при создании таблиц: {e}")

    # Добавление нового столбца target_gender, если он не существует
    try:
        await conn.execute(CREATE_TARGET_GENDER)
    except asyncpg.PostgresError as e:
        pass

    # Добавление нового столбца last_activity, если он не существует
    try:
        await conn.execute(CREATE_LAST_ACTIVITY)
    except asyncpg.PostgresError as e:
        pass

    # Добавление нового столбца username, если он не существует
    try:
        await conn.execute(CREATE_USERNAME)
    except asyncpg.PostgresError as e:
        pass

    # Добавление нового столбца message_count, если он не существует
    try:
        await conn.execute(CREATE_MESSAGE_COUNT)
    except asyncpg.PostgresError as e:
        pass

    # Очищаем таблицу лайков при каждом запуске бота
    #await conn.execute(DELETE_LIKES)
    #conn.commit()  # Подтверждаем изменения в базе данных
    await conn.close()   # Закрываем соединение с базой данных


    # Объект бота и диспетчера
    bot = Bot(token=os.getenv('BOT_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_routers(router, admin)

    # Настройка логирования
    logging.basicConfig(filename='bot.log', level=logging.INFO)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
