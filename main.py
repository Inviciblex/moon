import asyncio
import logging
import sys
import sqlite3
import datetime  # Не забудьте импортировать datetime
from aiogram.fsm.storage.memory import MemoryStorage
import config
import os
from aiogram.types import InputFile
from aiogram import F
from aiogram.types import FSInputFile
from aiogram.filters import Command
from aiogram import Bot, Dispatcher, types
from app.handlers import router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import subprocess
from datetime import datetime, timedelta
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Выполняем команду pip freeze и сохраняем список зависимостей в requirements.txt
"""def generate_requirements():
    try:
        # Открываем файл requirements.txt для записи
        with open('requirements.txt', 'w') as f:
            # Выполняем команду pip freeze и записываем результат в файл
            subprocess.run(['pip', 'freeze'], stdout=f)
        print("Файл requirements.txt успешно создан.")
    except Exception as e:
        print(f"Произошла ошибка при создании requirements.txt: {e}")
"""
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

def update_last_activity(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    current_time = datetime.datetime.now().isoformat()
    cursor.execute("UPDATE profiles SET last_activity = ? WHERE user_id = ?", (current_time, user_id))
    conn.commit()
    conn.close()

# Настройка логирования


async def main() -> None:
    # Подключение к базе данных SQLite
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Добавление нового столбца target_gender, если он не существует
    try:
        cursor.execute("ALTER TABLE profiles ADD COLUMN target_gender TEXT")
    except sqlite3.OperationalError:
        pass

    # Добавление нового столбца last_activity, если он не существует
    try:
        cursor.execute("ALTER TABLE profiles ADD COLUMN last_activity TEXT")
    except sqlite3.OperationalError:
        pass

    # Добавление нового столбца username, если он не существует
    try:
        cursor.execute("ALTER TABLE profiles ADD COLUMN username TEXT")
    except sqlite3.OperationalError:
        pass

    # Добавление нового столбца message_count, если он не существует
    try:
        cursor.execute("ALTER TABLE profiles ADD COLUMN message_count INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Создание таблицы профилей, если она не существует
    cursor.execute("""CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        description TEXT,
        photo_id TEXT,
        target_gender TEXT,  -- Пол, который ищет пользователь
        last_activity TEXT,  -- Новый столбец для активности
        username TEXT  -- Новый столбец для username
    )""")

    # Создание таблицы для хранения лайков, если она не существует
    cursor.execute("""CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        liked_user_id INTEGER NOT NULL,
        mutual BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (user_id) REFERENCES profiles (user_id),
        FOREIGN KEY (liked_user_id) REFERENCES profiles (user_id)
    )""")

    # Очищаем таблицу лайков при каждом запуске бота
    cursor.execute("DELETE FROM likes")
    conn.commit()  # Подтверждаем изменения в базе данных
    conn.close()   # Закрываем соединение с базой данных

    # Объект бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    # Список администраторов по user_id
    ADMINS = [839693861, 302808230]

    # Функция для проверки, является ли пользователь администратором
    async def is_admin(user_id: int) -> bool:
        return user_id in ADMINS

    # Обработчик команды /db для администраторов
    @dp.message(Command(commands=["db"]))
    async def send_db_file(message: types.Message):
        user_id = message.from_user.id

        # Проверяем, является ли пользователь администратором
        if await is_admin(user_id):
            try:
                # Путь к файлу базы данных
                db_file_path = "users.db"  # Убедитесь, что файл существует в этой директории
                db_file = FSInputFile(db_file_path)

                # Отправляем файл администратору
                await message.answer_document(db_file)
                await message.answer("📌📌📌Вот ваша база данных, админ! 😉")
            except Exception as e:
                await message.answer(f"Произошла ошибка при отправке файла: {e}")
        else:
            # Если пользователь не администратор
            await message.answer("Эта команда доступна только администраторам!")

    # Настройка логирования
    logging.basicConfig(filename='bot.log', level=logging.INFO)

    # Проверка, является ли пользователь администратором
    async def is_admin(user_id):
        # Здесь должна быть ваша логика для проверки админов
        return user_id in ADMINS

    # Обработчик команды /logs для администраторов
    @router.message(Command(commands=["logs"]))
    async def send_logs_command(message: types.Message):
        user_id = message.from_user.id

        # Проверяем, является ли пользователь администратором
        if await is_admin(user_id):
            try:
                # Путь к файлу логов
                log_file_path = "bot.log"  # Убедитесь, что файл существует в этой директории
                log_file = FSInputFile(log_file_path)  # Создаем FSInputFile

                # Отправляем файл администратору
                await message.answer_document(log_file)
                await message.answer("📌📌📌Вот ваши логи, админ! 😉")
            except Exception as e:
                await message.answer(f"Произошла ошибка при отправке файла: {e}")
        else:
            # Если пользователь не администратор
            await message.answer("Эта команда доступна только администраторам!")

    # Обработчик для команды /command
    @router.message(Command("command"))
    async def command_handler(message: types.Message):
        if message.from_user.id in ADMINS:
            commands_list = (
                "/logs - отправить логи\n"
                "/db - отправить базу данных\n"
                "/text - отправить сообщение от админа пользователю\n"
                "/notext - отмена отправки сообщения\n"
                "/broadcast - рассылка\n"
                "/nobroadcast - отмена рассылки\n"
                "/stats - статистика бота"  # Добавлено здесь
            )
            await message.answer(f"Команды для администраторов:\n{commands_list}")
        else:
            await message.answer("У вас нет прав на выполнение этой команды.")

    # Обработчик команды /stats
    @router.message(Command("stats"))
    async def stats_handler(message: types.Message):
        if message.from_user.id in ADMINS:
            # Подключение к базе данных SQLite
            conn = sqlite3.connect("users.db")

            cursor = conn.cursor()

            # Общее количество зарегистрированных пользователей
            cursor.execute("SELECT COUNT(*) FROM profiles")
            total_users = cursor.fetchone()[0]

            # Определяем активных пользователей
            now = datetime.now()
            day_ago = now - timedelta(days=1)
            week_ago = now - timedelta(weeks=1)
            month_ago = now - timedelta(weeks=4)

            # Преобразуем даты в строковый формат
            day_ago_str = day_ago.strftime("%Y-%m-%d %H:%M:%S")
            week_ago_str = week_ago.strftime("%Y-%m-%d %H:%M:%S")
            month_ago_str = month_ago.strftime("%Y-%m-%d %H:%M:%S")

            # Пользователи, активные за последний день
            cursor.execute("SELECT COUNT(*) FROM profiles WHERE last_activity >= ?", (day_ago_str,))
            active_users_day = cursor.fetchone()[0]

            # Пользователи, активные за последнюю неделю
            cursor.execute("SELECT COUNT(*) FROM profiles WHERE last_activity >= ?", (week_ago_str,))
            active_users_week = cursor.fetchone()[0]

            # Пользователи, активные за последний месяц
            cursor.execute("SELECT COUNT(*) FROM profiles WHERE last_activity >= ?", (month_ago_str,))
            active_users_month = cursor.fetchone()[0]

            # Количество отправленных сообщений за всё время
            cursor.execute("SELECT SUM(message_count) FROM profiles")
            total_messages = cursor.fetchone()[0] or 0  # Обработка случая, если нет сообщений

            # Средний возраст пользователей
            cursor.execute("SELECT AVG(age) FROM profiles")
            avg_age = cursor.fetchone()[0] or 0  # Обработка случая, если нет возрастов
            avg_age_range = f"{int(avg_age) - 5}-{int(avg_age) + 5} лет" if avg_age > 0 else "Нет данных"

            # Проверка значений для отладки
            print(f"day_ago: {day_ago_str}, week_ago: {week_ago_str}, month_ago: {month_ago_str}")
            print(f"Active users day: {active_users_day}, week: {active_users_week}, month: {active_users_month}")
            print(
                f"Messages day: total: {total_messages}")

            # Время наибольшей активности
            cursor.execute(
                "SELECT strftime('%H:00', last_activity) AS hour, COUNT(*) FROM profiles GROUP BY hour ORDER BY COUNT(*) DESC LIMIT 1"
            )
            result = cursor.fetchone()  # Сохраняем результат в переменную

            # Проверяем, есть ли данные и устанавливаем peak_activity_time
            peak_activity_time = result[0] + ":00" if result else "Нет данных"

            # Закрываем соединение
            conn.close()

            # Формируем сообщение
            stats_message = (
                f"📊 Статистика бота:\n"
                f"👥 Количество зарегистрированных пользователей: {total_users}\n"
                f"🟢 Количество активных пользователей (за день): {active_users_day}\n"
                f"🟢 Количество активных пользователей (за неделю): {active_users_week}\n"
                f"🟢 Количество активных пользователей (за месяц): {active_users_month}\n"
                f"✉️ Количество отправленных сообщений (за всё время, при удалении\редактировании анкеты счетчик смс сбрасывется): {total_messages}\n"
                f"👤 Средний возраст пользователей: {avg_age_range}\n"
                f"⏰ Время наибольшей активности: {peak_activity_time}\n"
            )

            await message.answer(stats_message)
        else:
            await message.answer("У вас нет прав на выполнение этой команды.")


    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
