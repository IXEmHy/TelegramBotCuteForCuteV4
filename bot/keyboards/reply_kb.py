"""
Reply клавиатуры убраны
Используется только встроенное меню команд Telegram
"""

from aiogram.types import ReplyKeyboardRemove


def get_user_main_keyboard() -> ReplyKeyboardRemove:
    """Убираем клавиатуру у пользователей"""
    return ReplyKeyboardRemove()


def get_admin_main_keyboard() -> ReplyKeyboardRemove:
    """Убираем клавиатуру у админа"""
    return ReplyKeyboardRemove()
