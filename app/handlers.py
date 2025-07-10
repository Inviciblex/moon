import logging
from aiogram.fsm.context import FSMContext
from aiogram import Bot, types, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import app.keyboards as kb
import config
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.keyboards import edit_or_delete_keyboard
from app.keyboards import after_registration_keyboard
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError
from config import ADMINS
from database.create import SAVE_FORM
from database.queries import *
from database.connection import connection
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

from app.keyboards import update_buttons_after_dislike  # Импорт дизлайка... Иначе он не работал

#conn = await connection()
#cursor = conn.cursor()
router = Router()
bot = Bot(token=os.getenv('BOT_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))



async def update_message_count(user_id: int):
    conn = await connection()
    # Обновление количества отправленных сообщений для пользователя
    await conn.execute(UPDATE_MESSAGE_COUNT, user_id)
    # Сохранение изменений и закрытие соединения
    await conn.close()


async def update_last_activity(user_id):
    conn = await connection()
    current_time = datetime.now().isoformat()  # Получаем текущее время
    await conn.execute(UPDATE_LAST_ACTIVITY, current_time, user_id)
    await conn.close()  # Закрываем соединение с базой данных


async def get_user_info(user_id):
    conn = await connection()
    result = await conn.fetchrow(GET_USER_INFO, user_id)
    #result = conn.fetchone()
    if result:
        return {
            'name': result[0],
            'age': result[1],
            'description': result[2],
            'photo_id': result[3]
        }
    return None  # Возвращаем None, если пользователь не найден


async def reset_likes(user_id):
    conn = await connection()

    # Удаляем лайки, которые пользователь поставил
    await conn.execute(DELETE_SELF_LIKE, user_id)

    # Удаляем лайки, которые были поставлены на анкеты этого пользователя
    await conn.execute(DELETE_SEND_LIKE, user_id)

    await conn.close()


# Состояния регистрации
class RegistrationStates(StatesGroup):
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_target_gender = State()  # Состояние для выбора, кого пользователь ищет
    waiting_for_photo = State()


# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id  # Получаем ID пользователя
    await update_last_activity(user_id)  # Обновляем время активности
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)

    await message.answer(
        "Привет, чудо в человеческом обличье! 🤩 Я бот для знакомств. Нажмите 'РЕГИСТРАЦИЯ', чтобы создать свою анкету!",
        reply_markup=await kb.start_keyboard()
    )
    await message.answer(
        "Я помогу вам найти друзей и, возможно, даже любовь! ❤️ "
        "После регистрации ваша анкета будет доступна другим пользователям, и если ваши интересы совпадут, вы сможете общаться и знакомиться!"
    )


# Хэндлер на кнопку "РЕГИСТРАЦИЯ"
@router.message(lambda message: message.text == "РЕГИСТРАЦИЯ")
async def cmd_register(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя
    username = message.from_user.username  # Получаем username пользователя
    await update_last_activity(user_id)  # Обновляем время активности
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)
    await reset_likes(user_id)     # Сбрасываем лайки перед редактированием анкеты

    await state.set_state(RegistrationStates.waiting_for_gender)  # Устанавливаем состояние
    await message.answer("Какой у вас пол? Выберите вариант:", reply_markup=await kb.gender_keyboard())

    # Сохраняем username в состоянии, чтобы потом добавить в базу данных
    await state.update_data(username=username)

# Обработка выбора пола
@router.message(RegistrationStates.waiting_for_gender)
async def process_gender(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя
    await update_last_activity(user_id)  # Обновляем время активности
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)

    gender = message.text.strip()
    if gender in ["М", "Ж"]:
        await state.update_data(gender=gender)  # Сохраняем пол в состоянии
        await state.set_state(RegistrationStates.waiting_for_age)  # Переходим к следующему шагу
        # Убираем клавиатуру после выбора пола
        await message.answer(
            "Отлично! 🎉 Теперь введите свой возраст. Пожалуйста, напишите число от 12 до 80!",
            reply_markup=types.ReplyKeyboardRemove()  # Убираем клавиши
        )
    else:
        await message.answer("Пожалуйста, выберите 'М' или 'Ж'.")


# Обработка возраста
@router.message(RegistrationStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя
    await update_last_activity(user_id)  # Обновляем время активности
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)

    if message.text.isdigit():
        age = int(message.text)
        if 12 <= age <= 80:
            await state.update_data(age=age)  # Сохраняем возраст в состоянии
            await state.set_state(RegistrationStates.waiting_for_name)  # Переходим к следующему шагу
            await message.answer("Отлично! 🎉 Теперь введите свое имя. Как вас зовут?")
        else:
            await message.answer(
                "Ой-ой! 🤔 Пожалуйста, введите корректный возраст (число от 12 до 80). Не обманывайте меня! 😄")
    else:
        await message.answer("Пожалуйста, введите корректный возраст (число от 12 до 80). Попробуйте снова!")


# Хэндлер на ввод имени
@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя
    await update_last_activity(user_id)  # Обновляем время активности
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)

    name = message.text.strip()  # Убираем лишние пробелы
    if name:  # Проверяем, что имя не пустое
        await state.update_data(name=name)  # Сохраняем имя в состоянии
        await state.set_state(RegistrationStates.waiting_for_description)  # Переходим к следующему шагу
        await message.answer(
            "Спасибо, что представились! 🙌 Теперь напишите описание к анкете. Чем вы увлекаетесь? Каковы ваши мечты?")
    else:
        await message.answer("Имя не может быть пустым! Пожалуйста, введите свое имя.")


# Хэндлер на ввод описания
@router.message(RegistrationStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя
    await update_last_activity(user_id)  # Обновляем время активности
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)

    description = message.text.strip()  # Убираем лишние пробелы
    if description:  # Проверяем, что описание не пустое
        await state.update_data(description=description)  # Сохраняем описание в состоянии
        await state.set_state(RegistrationStates.waiting_for_target_gender)  # Переходим к следующему шагу
        await message.answer("Отлично! Теперь выберите, кого вы ищете: мужчину (М) или женщину (Ж):",
                             reply_markup=await kb.target_gender_keyboard())
    else:
        await message.answer("Описание не может быть пустым! Пожалуйста, напишите о себе.")


# Обработка выбора кого искать
@router.message(RegistrationStates.waiting_for_target_gender)
async def process_target_gender(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя
    await update_last_activity(user_id)  # Обновляем время активности
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)

    target_gender = message.text.strip()
    if target_gender in ["М", "Ж"]:
        await state.update_data(target_gender=target_gender)  # Сохраняем кого ищет пользователь
        await state.set_state(RegistrationStates.waiting_for_photo)  # Переходим к следующему шагу
        await message.answer("Отлично! 🎉 Теперь отправьте свою фотографию.",
                             reply_markup=types.ReplyKeyboardRemove())  # Убираем клавиши
    else:
        await message.answer("Пожалуйста, выберите 'М' или 'Ж'.")


# Обработка фотографии
@router.message(RegistrationStates.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя
    conn = await connection()
    await update_last_activity(user_id)  # Обновляем время активности
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)

    photo_id = message.photo[-1].file_id  # Получаем ID самой большой версии фото
    data = await state.get_data()  # Получаем все данные из состояния
    user_id = message.from_user.id

    # Получаем @username
    username = message.from_user.username  # Получаем имя пользователя

    # Сохранение анкеты в базу данных
    await conn.execute(
        SAVE_FORM,
            user_id,
            data['name'],
            data['age'],
            data['gender'],
            data['description'],
            photo_id,
            data['target_gender'],
            username
    )
    await conn.close()

    # Завершение регистрации и отправка анкеты с фотографией
    await bot.send_photo(
        chat_id=user_id,
        photo=photo_id,
        caption=(f"Вы зарегистрировали анкету:\n\nИмя: {data['name']}\n"
                 f"Возраст: {data['age']}\nПол: {data['gender']}\n"
                 f"Описание: {data['description']}\n"
                 f"Ищет: {data['target_gender']}\n"
                 f"Теперь вы можете начать искать и знакомиться!"),
        reply_markup=await kb.after_registration_keyboard()
    )

    # Добавляем дополнительное сообщение с информацией о городе
    additional_message = (
        "❗️❗️ Обратите внимание, что город НЕ указывается, "
        "поскольку знакомства происходят только в городе Краснодар. "
        "При создании и поиске анкет вы подтверждаете, что находитесь в Краснодаре и ищете человека с этого же города. ❗️❗️\n\n"
        "❓❓ Если вы находитесь в другом городе - не переживайте, скоро будет доступен бот и для вашего города. ❓❓\n\n"
        "✅ Эта и вся другая информация будет опубликована в нашем telegram-канале. ✅"
    )

    await message.answer(additional_message)

    await state.clear()  # Очищаем состояние

#import random


# Определение состояний
class PrivateMessageState(StatesGroup):
    waiting_for_username = State()
    waiting_for_message_text = State()

# Функция для получения ID пользователя по username (пример)
async def get_user_id_by_username(username):
    conn = await connection()
    result = await conn.fetchrow(GET_ID_BY_USERNAME, username)
    await conn.close()
    return result[0] if result else None


# Обработчик команды /text для админов
@router.message(Command("text"))
async def private_message_command(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer(
            "Введите @username пользователя, которому хотите отправить сообщение, или введите /notext для отмены."
        )
        await state.set_state(PrivateMessageState.waiting_for_username)  # Устанавливаем состояние ожидания username
    else:
        await message.answer("У вас нет прав на выполнение этой команды.")

# Обработчик команды /notext для отмены
@router.message(Command("notext"), PrivateMessageState.waiting_for_username)
async def cancel_private_message_command(message: types.Message, state: FSMContext):
    await state.clear()  # Сбрасываем состояние
    await message.answer("Отправка личного сообщения отменена.")

# Обработчик для получения @username
@router.message(PrivateMessageState.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text.strip()
    if not username.startswith("@"):
        await message.answer("Пожалуйста, введите корректный @username.")
        return

    user_id = await get_user_id_by_username(username[1:])  # Убираем символ '@'
    if user_id:
        await state.update_data(user_id=user_id)  # Сохраняем user_id в состоянии
        await message.answer("Введите текст сообщения или отправьте фото с текстом, или введите /notext для отмены.")
        await state.set_state(PrivateMessageState.waiting_for_message_text)  # Устанавливаем состояние ожидания текста сообщения
    else:
        await message.answer(
            f"Пользователь с username {username} не найден. Попробуйте снова или введите /notext для отмены."
        )

# Обработчик для получения текста сообщения или фото
@router.message(PrivateMessageState.waiting_for_message_text)
async def process_message_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")

    if user_id:
        if message.photo:  # Если сообщение содержит фото
            photo_id = message.photo[-1].file_id  # Получаем ID самого большого фото
            caption = message.caption if message.caption else "Личное сообщение от администратора."
            full_caption = f"Личное сообщение от администратора: {caption}"
            try:
                await bot.send_photo(user_id, photo=photo_id, caption=full_caption)
                await message.answer("Сообщение с фото успешно передано пользователю.")
            except Exception as e:
                await message.answer(f"Не удалось отправить сообщение с фото: {e}")
        else:  # Если текстовое сообщение
            message_text = message.text.strip()
            full_message = f"Личное сообщение от администратора: {message_text}"
            try:
                await bot.send_message(user_id, full_message)
                await message.answer("Сообщение успешно передано пользователю.")
            except Exception as e:
                await message.answer(f"Не удалось отправить сообщение: {e}")
    else:
        await message.answer("Ошибка при получении ID пользователя.")

    await state.clear()  # Очищаем состояние


# Состояния для команды /broadcast
class BroadcastState(StatesGroup):
    waiting_for_message = State()


# Функция для получения всех ID пользователей из базы данных
async def get_all_user_ids():
    conn = await connection()
    user_ids = await conn.fetch()
    #user_ids = [row[0] for row in conn.fetchall()]
    return user_ids


# Функция для удаления анкеты пользователя
async def delete_user_profile(user_id):
    conn = await connection()
    await conn.execute(DELETE_FORM, user_id)
    await conn.close()


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.message(Command("broadcast"))
async def broadcast_command(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMINS:
        await message.answer(
            "Введите сообщение для рассылки или отправьте фото с текстом, или введите /nobroadcast для отмены.")
        await state.set_state(BroadcastState.waiting_for_message)  # Устанавливаем состояние ожидания
    else:
        await message.answer("У вас нет прав на выполнение этой команды.")


# Обработчик команды /nobroadcast для отмены рассылки
@router.message(Command("nobroadcast"), BroadcastState.waiting_for_message)
async def cancel_broadcast_command(message: types.Message, state: FSMContext):
    await state.clear()  # Завершаем состояние
    await message.answer("Рассылка сообщения отменена.")


# Обработчик отправки сообщения для рассылки
@router.message(BroadcastState.waiting_for_message)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    # Получаем текст сообщения
    broadcast_text = message.text if message.text else ""

    # Получаем список всех пользователей
    user_ids = await get_all_user_ids()

    # Отправляем сообщение всем пользователям
    for user_id in user_ids:
        try:
            if message.photo:  # Если сообщение содержит фото
                photo_id = message.photo[-1].file_id  # Получаем ID самого большого фото
                caption = message.caption if message.caption else broadcast_text
                await bot.send_photo(user_id, photo=photo_id, caption=caption)
            else:  # Если текстовое сообщение
                await bot.send_message(user_id, broadcast_text)
        except TelegramForbiddenError:
            logger.warning(f"Пользователь {user_id} заблокировал бота.")
            await delete_user_profile(user_id)  # Удаляем анкету пользователя
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

    await message.answer("Сообщение успешно разослано всем пользователям.")
    await state.clear()  # Завершаем состояние

# Обработка нажатия кнопки "Поиск"
@router.message(lambda message: message.text == "🔍Поиск")
async def cmd_search(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await update_last_activity(user_id)  # Обновляем время активности пользователя
    await update_message_count(user_id)  # Обновление количества отправленных сообщений
    conn = await connection()
    # Получаем данные состояния
    data = await state.get_data()
    viewed_profiles = data.get("viewed_profiles", [])  # Получаем список просмотренных анкет

    # Получаем пол, возраст и предпочтения пользователя
    user = await conn.fetchrow(GET_USER_DATA, user_id)
    #user = cursor.fetchone()

    if user is None:
        await message.answer("Сначала нужно зарегистрироваться. Нажмите 'РЕГИСТРАЦИЯ' для создания анкеты.")
        return

    user_gender = user[0]  # Пол пользователя
    target_gender = user[1]  # Пол, который пользователь ищет
    user_age = user[2]  # Возраст пользователя

    # Устанавливаем возрастной диапазон ±5 лет
    max_age = user_age + 5
    min_age = user_age - 5

    # Получаем дату и время, когда пользователь был активен в последний раз
    one_week_ago = datetime.now() - timedelta(weeks=2)
    one_week_ago_str = one_week_ago.strftime("%Y-%m-%d %H:%M:%S")

    # Ищем анкеты противоположного пола и по возрасту, исключая уже просмотренные анкеты
    profile = await conn.fetchrow(
        SEARCH_FORMS.format(','.join(['%7'] * len(viewed_profiles)) if viewed_profiles else 'NULL'),
        user_id, target_gender, user_gender, min_age, max_age, one_week_ago_str, *viewed_profiles
    )
    #profile = cursor.fetchone()

    # Если анкета найдена
    if profile:
        profile_id = profile[0]

        # Добавляем ID анкеты в список просмотренных
        viewed_profiles.append(profile_id)
        await state.update_data(viewed_profiles=viewed_profiles)

        last_activity = profile[7] if profile[7] else "Никогда"  # Получаем время активности, если оно есть

        # Отправляем анкету пользователю
        await bot.send_photo(
            chat_id=user_id,
            photo=profile[5],  # photo_id
            caption=(f"👋 {profile[1]}\n"  # имя
                     f"💕 {profile[2]}\n"  # возраст
                     f"📝 {profile[4]}\n"),
            reply_markup=await kb.like_dislike_buttons(profile[0], profile[7])  # Передаем ID анкеты в callback_data
        )
    else:
        # Если анкеты закончились, начинаем с начала (очищаем просмотренные анкеты)
        await state.update_data(viewed_profiles=[])
        await message.answer("Анкеты закончились, нажмите '🔍Поиск', чтобы начать просмотр заново.")

# Обработка инлайн-кнопки лайка
@router.callback_query(lambda call: call.data.startswith("like_"))
async def process_like_callback(call: types.CallbackQuery):
    liked_user_id = int(call.data.split("_")[1])  # ID пользователя, которому поставили лайк
    liked_username = call.data.split("_")[2]
    user_id = call.from_user.id
    user_name = call.from_user.username

    await update_last_activity(user_id)  # Обновляем время активности пользователя
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)

    conn = await connection()
    # Проверяем, лайкал ли этот пользователь ранее
    existing_like = await conn.fetchrow(CHECK_LIKE, user_id, liked_user_id)
    #existing_like = cursor.fetchone()

    if not existing_like:
        # Сохраняем лайк в базе данных
        await conn.execute(SAVE_LIKE,
                       user_id, liked_user_id, user_name, liked_username)

        # Проверяем, ставил ли лайк другой пользователь
        mutual_like = await conn.fetchrow(CHECK_LIKE, liked_user_id, user_id)
        #mutual_like = cursor.fetchone()

        if mutual_like:
            # Если лайк взаимный, отправляем сообщение обоим пользователям
            user_info = get_user_info(user_id)  # Информация о пользователе, который поставил лайк
            liked_user_info = get_user_info(liked_user_id)  # Информация о пользователе, который получил лайк

            # Уведомляем другого пользователя о взаимной симпатии и отправляем анкету
            mutual_message = (
                f"У вас взаимная симпатия❤️❤️❤️\n\n"
                f"👋 {user_info['name']}, {user_info['age']}\n"
                f"📝 {user_info['description']}\n\n"
                f"Вот ссылка на профиль: @{user_name}"
            )
            await bot.send_photo(
                liked_user_id, photo=user_info['photo_id'], caption=mutual_message
            )

            # Уведомляем первого пользователя о взаимной симпатии
            mutual_message_for_first_user = (
                f"У вас взаимная симпатия❤️❤️❤️\n\n"
                f"👋 {liked_user_info['name']}, {liked_user_info['age']}\n"
                f"📝 {liked_user_info['description']}\n\n"
                f"Вот ссылка на профиль: @{liked_username}"
            )
            await bot.send_photo(
                user_id, photo=liked_user_info['photo_id'], caption=mutual_message_for_first_user
            )

        else:
            # Убираем все инлайн-кнопки с сообщения
            await call.message.edit_reply_markup(reply_markup=None)

            # Отправляем уведомление понравившемуся пользователю с прикрепленным сообщением о лайке и анкетой
            user_info = get_user_info(user_id)  # Функция для получения информации о пользователе
            like_message = (
                f"❤️❤️❤️ Ой-ё... Этот пользователь поставил вам лайк! Оцените его в ответ.\n\n"
                f"👋 {user_info['name']}\n"
                f"💕 {user_info['age']}\n"
                f"📝 {user_info['description']}\n"
            )
            await bot.send_photo(
                liked_user_id, photo=user_info['photo_id'],
                caption=like_message,
                reply_markup=await kb.like_dislike_buttons(user_id, user_name)
            )


        # Отправляем сообщение пользователю о том, что лайк был поставлен
        await call.message.answer("❤️❤️❤️ Вы поставили лайк!")
    else:
        await call.message.answer("Вы уже поставили лайк этому пользователю!")

        # Убираем инлайн-кнопки из сообщения пользователя, который поставил лайк
        await call.message.edit_reply_markup(reply_markup=None)

 # Уведомляем пользователя о кнопке "Поиск"
    await call.message.answer("Чтобы увидеть новую анкету, нажмите '🔍Поиск'.")

# Определяем состояние для жалобы
class ComplaintState(StatesGroup):
    waiting_for_complaint_text = State()

# Обработка нажатия кнопки "Пожаловаться"
@router.callback_query(lambda call: call.data.startswith("report_"))
async def process_report_callback(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    report_user_id = int(call.data.split("_")[1])  # ID пользователя, на которого жалуются

    await update_last_activity(user_id)  # Обновляем время активности пользователя
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)

    # Убираем все инлайн-кнопки с текущего сообщения
    await call.message.edit_reply_markup(reply_markup=None)

    # Запрос текста жалобы
    await call.message.answer(
        "Напишите в чем состоит жалоба? Может непристойная фотография, оскорбляющий текст или что-то другое? Я передам вашу жалобу сразу администратору и он примет правильные меры.",
        reply_markup=ReplyKeyboardRemove())

    # Сохраняем ID пользователя, на которого жалуются, и переводим бота в состояние ожидания текста
    await state.update_data(report_user_id=report_user_id)
    await state.set_state(ComplaintState.waiting_for_complaint_text)


# Обработка текста жалобы
@router.message(ComplaintState.waiting_for_complaint_text)
async def process_complaint_text(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    report_user_id = user_data['report_user_id']  # ID пользователя, на которого жалуются
    complaint_text = message.text  # Текст жалобы

    # Обновляем время активности пользователя
    await update_last_activity(message.from_user.id)

    conn = await connection()
    # Получите информацию о пользователе, на которого жалуются
    reported_user = await conn.fetchrow(
        REPORTED_USER,
        report_user_id)
    #reported_user = cursor.fetchone()

    if reported_user:
        reported_name, reported_username, gender, age, description, photo_id, target_gender = reported_user
        # Получите информацию о лайках для этого пользователя
        like_info = await conn.fetchrow(LIKE_INFO,
                       report_user_id)
        #like_info = cursor.fetchone()

        if like_info:
            liked_user_id, liked_name = like_info[1], like_info[2]  # Извлекаем liked_user_id и liked_name
        else:
            liked_user_id = liked_name = None  # Нет информации о лайках

        # Формируем сообщение
        report_message = (
            f"📌📌📌Пользователь @{message.from_user.username} пожаловался на @{reported_username}:\n\n"
            f"👤 Имя: {reported_name}\n"
            f"🔢 Возраст: {age}\n"
            f"🚻 Пол: {gender}\n"
            f"📝 Описание: {description}\n"
            f"💖 Целевой пол: {target_gender}\n\n"
            f"📌 ID пользователя: {report_user_id}\n"
            f"📸 Фото пользователя: {photo_id}\n"  # photo_id из профиля
            f"💬 ID пользователя, который поставил лайк: {liked_user_id}\n"
            f"💖 Имя пользователя, который поставил лайк: {liked_name}\n"
            f"Текст жалобы: {complaint_text}\n"
        )

        # Отправить сообщение администраторам с фотографией
        for admin_id in config.ADMINS:
            if photo_id:
                await bot.send_photo(admin_id, photo=photo_id, caption=report_message)
            else:
                await bot.send_message(admin_id, report_message)

        # Сообщаем пользователю, что жалоба была передана
        await message.answer("📬📬📬Жалоба уже передана, продолжайте поиск анкет.")

        # Возвращаем кнопки "Поиск" и "Моя анкета"
        from app.keyboards import after_registration_keyboard
        await message.answer("Что хотите делать дальше?", reply_markup=await after_registration_keyboard())
    else:
        await message.answer("Не удалось найти информацию о пользователе.")

    # Сбрасываем состояние
    await state.clear()

 # Уведомляем пользователя о кнопке "Поиск"
    await message.answer("Чтобы увидеть новую анкету, нажмите '🔍Поиск'.")


# Обработка кнопки "Дизлайк"
@router.callback_query(lambda call: call.data.startswith("dislike_"))
async def process_dislike_callback(call: types.CallbackQuery):
    disliked_user_id = int(call.data.split("_")[1])  # Получаем ID дизлайкнутого пользователя
    liked_name = call.data.split("_")[2]  # Получаем имя лайкнутого пользователя

    await update_last_activity(call.from_user.id)  # Обновляем время активности пользователя

    # Отправляем сообщение в чат
    await call.message.answer("👎👎👎 Вы поставили Дизлайк!")

    # Убираем все инлайн-кнопки с текущего сообщения
    await call.message.edit_reply_markup(reply_markup=None)

    # Уведомляем пользователя о кнопке "Поиск"
    await call.message.answer("Чтобы увидеть новую анкету, нажмите '🔍Поиск'.")

    # Закрываем callback-запрос
    await call.answer()

# Обработка нажатия кнопки "Моя анкета"
@router.message(lambda message: message.text == "📑Моя анкета")
async def cmd_my_profile(message: types.Message):
    user_id = message.from_user.id

    await update_last_activity(user_id)  # Обновляем время активности пользователя
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)
    conn = await connection()
    # Получаем анкету пользователя из базы данных
    profile = await conn.fetchrow(FORM_INFO, user_id)
    #profile = cursor.fetchone()
    await conn.close()
    if profile:
        name, age, description, gender, target_gender, photo_id = profile

        # Отправляем информацию об анкете в одном сообщении
        await message.answer_photo(
            photo=photo_id,
            caption=f"👤 Имя: {name}\n"
                    f"🎂 Возраст: {age}\n"
                    f"📝 Описание: {description}\n"
                    f"🔹 Пол: {gender}\n"
                    f"🔸 Ищет: {target_gender}"
        )

        # Отправляем второе сообщение с пояснением
        await message.answer("Желаете изменить или удалить анкету? Если нет, можете при помощи кнопки '↪️Назад' вернуться к поиску анкет!",
                             reply_markup=await edit_or_delete_keyboard())
    else:
        await message.answer("Анкета не найдена. Пожалуйста, зарегистрируйтесь!", reply_markup=await kb.start_keyboard())

# Обработка нажатия кнопки "Редактировать анкету"
@router.message(lambda message: message.text == "✏️Редактировать анкету")
async def cmd_edit_profile(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await update_last_activity(user_id)  # Обновляем время активности пользователя
    await reset_likes(user_id)     # Сбрасываем лайки перед редактированием анкеты
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)

    await state.set_state(RegistrationStates.waiting_for_gender)  # Сбрасываем состояние
    await message.answer("Давайте начнем с выбора пола. Какой у вас пол?", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="М"), KeyboardButton(text="Ж")]],
        resize_keyboard=True
    ))

# Обработка нажатия кнопки "Удалить анкету"
@router.message(lambda message: message.text == "✂️Удалить анкету")
async def cmd_delete_profile(message: types.Message):
    user_id = message.from_user.id
    await update_last_activity(user_id)  # Обновляем время активности пользователя
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)
    conn = await connection()

    await conn.execute(DELETE_FORM, user_id)
    await conn.close()
    await message.answer("Ваша анкета была успешно удалена! Если хотите, можете зарегистрироваться заново.",
                         reply_markup=await kb.start_keyboard())

# Обработка нажатия кнопки "Назад"
@router.message(lambda message: message.text == "↪️Назад")
async def cmd_back_to_search(message: types.Message):
    user_id = message.from_user.id
    await update_last_activity(user_id)  # Обновляем время активности пользователя
    # Обновление количества отправленных сообщений
    await update_message_count(user_id)

    await message.answer("Вы вернулись к поиску анкет. Нажмите '🔍Поиск', чтобы начать просмотр анкет.",
                         reply_markup=await after_registration_keyboard())


# Состояние для отправки сообщения модераторам
class ModeratorMessageState(StatesGroup):
    waiting_for_message = State()


# Обработчик для команды /start
@router.message(Command("start"))
async def start_command_handler(message: types.Message):
    await message.answer(
        "Добро пожаловать! Вы можете отправить письмо администраторам, используя кнопку ниже.",
        reply_markup=await after_registration_keyboard()
    )


# Обработчик для кнопки "Письмо администраторам"
@router.message(lambda message: message.text == "📩Письмо администраторам")
async def send_message_to_moderators(message: types.Message, state: FSMContext):
    await message.answer("📬📬📬Что вы хотите сообщить администраторам?")

    # Удаляем клавиатуру, чтобы скрыть кнопки
    await message.answer(" Напишите, пожалуйста, я все передам.", reply_markup=types.ReplyKeyboardRemove())

    await state.set_state(ModeratorMessageState.waiting_for_message)

# Обработчик для получения сообщения от пользователя
@router.message(ModeratorMessageState.waiting_for_message)
async def process_moderator_message(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    ticket_number = user_data.get("ticket_number", 1)
    username = message.from_user.username or message.from_user.full_name

    # Определяем содержание сообщения (текст и/или фото)
    if message.photo:
        photo_id = message.photo[-1].file_id
        caption = message.caption if message.caption else "Нет текста"
        report_text = f"📌📌📌Тикет {ticket_number} от пользователя @{username}: {caption}"
        # Отправляем фото с текстом администраторам
        for admin_id in ADMINS:
            await bot.send_photo(admin_id, photo=photo_id, caption=report_text)
    else:
        report_text = f"📌📌📌Тикет {ticket_number} от пользователя @{username}: {message.text}"
        # Отправляем текст администраторам
        for admin_id in ADMINS:
            await bot.send_message(admin_id, report_text)

    # Уведомляем пользователя
    await message.answer("Спасибо, уже передал, если это действительно очень важно, то с вами свяжутся.")

    # Обновляем и сохраняем номер тикета
    await state.update_data(ticket_number=ticket_number + 1)
    await state.clear()

    # Показываем клавиатуру обратно
    await message.answer("Продолжаем Поиск?", reply_markup=await after_registration_keyboard())