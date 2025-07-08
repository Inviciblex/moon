from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Клавиатура для стартового меню
async def start_keyboard():
    # Создание кнопок
    buttons = [[KeyboardButton(text="РЕГИСТРАЦИЯ")]]
    start_keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return start_keyboard


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Клавиатура после регистрации с кнопками "Моя анкета" и "Письмо администраторам"
async def after_registration_keyboard():
    after_registration_buttons = [
        [KeyboardButton(text="🔍Поиск")],  # Кнопка "🔍Поиск"
        [KeyboardButton(text="📑Моя анкета")],  # Кнопка "📑Моя анкета"
        [KeyboardButton(text="📩Письмо администраторам")]  # Кнопка "📩Письмо администраторам"
    ]
    return ReplyKeyboardMarkup(keyboard=after_registration_buttons, resize_keyboard=True)

# Клавиатура для изменения анкеты или возврата
async def edit_or_delete_keyboard():
    buttons = [
        [KeyboardButton(text="✏️Редактировать анкету")],  # Кнопка для редактирования анкеты
        [KeyboardButton(text="✂️Удалить анкету")],  # Кнопка для удаления анкеты
        [KeyboardButton(text="↪️Назад")]  # Кнопка для возврата к поиску
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# Клавиатура для выбора пола
async def gender_keyboard():
    gender_buttons = [[KeyboardButton(text="М"), KeyboardButton(text="Ж")]]
    gender_keyboard = ReplyKeyboardMarkup(keyboard=gender_buttons, resize_keyboard=True)
    return gender_keyboard


# Клавиатура для выбора пола, кого ищет пользователь
async def target_gender_keyboard():
    target_gender_buttons = [[KeyboardButton(text="М"), KeyboardButton(text="Ж")]]
    target_gender_keyboard = ReplyKeyboardMarkup(keyboard=target_gender_buttons, resize_keyboard=True)
    return target_gender_keyboard


# Инлайн-кнопка для лайков (❤️) и дизлайков (👎)
async def like_dislike_buttons(liked_user_id, liked_name):
    keyboard = InlineKeyboardBuilder()

    # Кнопки Лайк и Дизлайк
    keyboard.add(InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{liked_user_id}_{liked_name}"))
    keyboard.add(InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"dislike_{liked_user_id}_{liked_name}"))

    # Кнопка Пожаловаться
    keyboard.add(InlineKeyboardButton(text="🚫 Пожаловаться", callback_data=f"report_{liked_user_id}"))

    # Возвращаем клавиатуру
    return keyboard.adjust(2).as_markup()


# Функция для обновления кнопок после нажатия "👎 Дизлайк" (только дизлайк и жалоба)
async def update_buttons_after_dislike(liked_user_id, liked_name):
    keyboard = InlineKeyboardBuilder()

    # Оставляем кнопки "👎 Дизлайк" и "🚫 Пожаловаться"
    keyboard.add(InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"dislike_{liked_user_id}_{liked_name}"))
    keyboard.add(InlineKeyboardButton(text="🚫 Пожаловаться", callback_data=f"report_{liked_user_id}"))

    return keyboard.adjust(2).as_markup()

# Функция, возвращающая только кнопку лайка
async def like_buttons(profile_id):
    keyboard = InlineKeyboardBuilder()  # Одна кнопка в ряд
    keyboard.add(
        InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{profile_id}")
    )
    return keyboard.adjust(1).as_markup()
