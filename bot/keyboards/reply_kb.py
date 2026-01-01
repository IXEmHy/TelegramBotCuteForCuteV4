"""
Reply клавиатуры (обычные кнопки)
Кнопки отправляют команды вместо текста
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_user_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура для обычного пользователя"""
    keyboard = [
        [KeyboardButton(text="/help")],
        [KeyboardButton(text="/stats")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите команду...",
    )


def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура для администратора"""
    keyboard = [
        [KeyboardButton(text="/help")],
        [KeyboardButton(text="/stats")],
        [KeyboardButton(text="/admin")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите команду...",
    )


def get_admin_exit_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выхода из админ-панели"""
    keyboard = [
        [KeyboardButton(text="/start")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
