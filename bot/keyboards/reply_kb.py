"""
Reply клавиатуры для бота (обычные кнопки внизу экрана)
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_user_main_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура пользователя"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✨ Использовать бота"),
            ],
            [
                KeyboardButton(text="📜 Список действий"),
            ],
            [
                KeyboardButton(text="📊 Моя статистика"),
                KeyboardButton(text="📖 Помощь"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура админа (те же кнопки, но логика может отличаться)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✨ Использовать бота"),
            ],
            [
                KeyboardButton(text="📜 Список действий"),
            ],
            [
                KeyboardButton(text="📊 Моя статистика"),
                KeyboardButton(text="📖 Помощь"),
            ],
            # Админские функции теперь через команды (/admin)
        ],
        resize_keyboard=True,
        input_field_placeholder="Режим администратора...",
    )
