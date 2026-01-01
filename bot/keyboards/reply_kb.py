"""
Reply клавиатуры (обычные кнопки)
Кнопки отображают красивый текст, но отправляют команды
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.core.commands import CMD


def get_user_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура для обычного пользователя"""
    keyboard = [
        [KeyboardButton(text=CMD.BTN_HELP_TEXT)],
        [KeyboardButton(text=CMD.BTN_STATS_TEXT)],
        [KeyboardButton(text=CMD.BTN_HOW_TO_USE_TEXT)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура для администратора"""
    keyboard = [
        [KeyboardButton(text=CMD.BTN_HELP_TEXT)],
        [KeyboardButton(text=CMD.BTN_STATS_TEXT)],
        [KeyboardButton(text=CMD.BTN_HOW_TO_USE_TEXT)],
        [KeyboardButton(text=CMD.BTN_ADMIN_STATS_TEXT)],
        [KeyboardButton(text=CMD.BTN_ADMIN_PANEL_TEXT)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def get_admin_exit_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выхода из админ-панели"""
    keyboard = [
        [KeyboardButton(text="⬅️ Выйти из админ-панели")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
