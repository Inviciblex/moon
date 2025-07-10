import datetime  # Не забудьте импортировать datetime
from config import ADMINS
from aiogram.types import FSInputFile
from aiogram.filters import Command
from aiogram import types, Router
from datetime import datetime, timedelta

from database.connection import connection
from database.queries import *


admin = Router()

async def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


# Обработчик команды /logs для администраторов
@admin.message(Command(commands=["logs"]))
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
@admin.message(Command("command"))
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
@admin.message(Command("stats"))
async def stats_handler(message: types.Message):
    if message.from_user.id in ADMINS:
        conn = await connection()

        #cursor = conn.cursor()

        # Общее количество зарегистрированных пользователей
        total_users = await conn.fetchval(TOTAL_USERS)
        #total_users = cursor.fetchone()[0]

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
        active_users_day = await conn.fetchval(ACTIVE_USERS, day_ago_str)
        #active_users_day = cursor.fetchone()[0]

        # Пользователи, активные за последнюю неделю
        active_users_week = await conn.fetchval(ACTIVE_USERS, week_ago_str)
        #active_users_week = cursor.fetchone()[0]

        # Пользователи, активные за последний месяц
        active_users_month = await conn.fetchval(ACTIVE_USERS, month_ago_str)
        #active_users_month = cursor.fetchone()[0]

        # Количество отправленных сообщений за всё время
        total_messages = await conn.fetchval(MESSAGES_TOTAL)
        #total_messages = cursor.fetchone()[0] or 0  # Обработка случая, если нет сообщений

        # Средний возраст пользователей
        avg_age = await conn.fetchval(AVG_AGE)
        #avg_age = cursor.fetchone()[0] or 0  # Обработка случая, если нет возрастов
        avg_age_range = f"{int(avg_age) - 5}-{int(avg_age) + 5} лет" if avg_age > 0 else "Нет данных"

        # Проверка значений для отладки
        print(f"day_ago: {day_ago_str}, week_ago: {week_ago_str}, month_ago: {month_ago_str}")
        print(f"Active users day: {active_users_day}, week: {active_users_week}, month: {active_users_month}")
        print(
            f"Messages day: total: {total_messages}")

        # Время наибольшей активности
        result = await conn.fetchval(ACTIVE_TIME)
        #result = cursor.fetchone()  # Сохраняем результат в переменную

        # Проверяем, есть ли данные и устанавливаем peak_activity_time
        peak_activity_time = result[0] + ":00" if result else "Нет данных"

        # Закрываем соединение
        await conn.close()

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
