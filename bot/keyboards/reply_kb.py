"""
Reply клавиатуры (обычные кнопки)
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.core.commands import CMD


def get_user_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура для обычного пользователя"""
    keyboard = [
        [KeyboardButton(text=CMD.BTN_ACTIONS)],
        [KeyboardButton(text=CMD.BTN_HOW_TO_USE)],
        [KeyboardButton(text=CMD.BTN_MY_STATS)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура для администратора"""
    keyboard = [
        [KeyboardButton(text=CMD.BTN_ACTIONS)],
        [KeyboardButton(text=CMD.BTN_HOW_TO_USE)],
        [KeyboardButton(text=CMD.BTN_MY_STATS)],
        [
            KeyboardButton(text=CMD.BTN_ADMIN_STATS),
            KeyboardButton(text=CMD.BTN_ADMIN_ACTIONS),
        ],
        [KeyboardButton(text=CMD.BTN_ADMIN_TEST)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def get_admin_exit_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выхода из админ-панели"""
    keyboard = [
        [KeyboardButton(text=CMD.BTN_ADMIN_EXIT)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
