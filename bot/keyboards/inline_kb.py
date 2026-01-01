"""
Inline клавиатуры для бота

Создает:
- Клавиатуру с выбором действий
- Клавиатуру для ответа (Принять/Отказаться)
- Клавиатуру главного меню
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.core.config import settings


def get_actions_keyboard(receiver_id: int) -> InlineKeyboardMarkup:
    """
    Создает inline клавиатуру с кнопками выбора действий

    Args:
        receiver_id: ID получателя действия

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками действий

    Формат callback_data: "action:{receiver_id}:{action_name}"
    """
    builder = InlineKeyboardBuilder()

    # Эмодзи для действий
    action_emojis = {
        "погладить": "🤗",
        "обнять": "🫂",
        "поцеловать": "💋",
        "ударить": "👊",
        "похвалить": "👏",
        "подмигнуть": "😉",
        "улыбнуться": "😊",
        "пнуть": "🦶",
    }

    for action in settings.actions:
        emoji = action_emojis.get(action.lower(), "✨")
        callback_data = f"action:{receiver_id}:{action}"
        builder.button(
            text=f"{emoji} {action.capitalize()}", callback_data=callback_data
        )

    # Размещаем кнопки по 2 в ряд
    builder.adjust(2)
    return builder.as_markup()


def get_response_keyboard(interaction_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для ответа на действие

    Args:
        interaction_id: ID взаимодействия в БД

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками "Принять" и "Отказаться"

    Формат callback_data: "respond:{interaction_id}:{accept|decline}"
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять", callback_data=f"respond:{interaction_id}:accept"
                ),
                InlineKeyboardButton(
                    text="❌ Отказаться",
                    callback_data=f"respond:{interaction_id}:decline",
                ),
            ]
        ]
    )
    return keyboard


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Создает главное меню бота (для команды /start)

    Returns:
        InlineKeyboardMarkup: Главное меню с кнопками
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✨ Попробовать бота", switch_inline_query="")],
            [
                InlineKeyboardButton(
                    text="📖 Как использовать", callback_data="show_tutorial"
                ),
                InlineKeyboardButton(
                    text="📊 Моя статистика", callback_data="show_stats"
                ),
            ],
        ]
    )
    return keyboard


def get_help_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для команды /help

    Returns:
        InlineKeyboardMarkup: Клавиатура с полезными ссылками
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Моя статистика", callback_data="show_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ Как использовать", callback_data="show_tutorial"
                )
            ],
        ]
    )
    return keyboard
