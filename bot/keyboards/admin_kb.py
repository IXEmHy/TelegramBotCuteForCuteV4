"""
Клавиатуры для админ-панели
"""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Главное меню админа"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👥 Статистика"),
                KeyboardButton(text="🔧 Управление действиями"),
            ],
            [
                KeyboardButton(text="🧪 Тест команд"),
                KeyboardButton(text="⬅️ Выйти"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Админ-панель",
    )


def get_actions_management_menu() -> InlineKeyboardMarkup:
    """Меню управления действиями"""
    builder = InlineKeyboardBuilder()

    builder.button(text="➕ Добавить действие", callback_data="admin:action:add")
    builder.button(text="✏️ Редактировать", callback_data="admin:action:list:1")
    builder.button(text="🗑 Удалить", callback_data="admin:action:delete_list:1")
    builder.button(text="🔄 Обновить кэш", callback_data="admin:cache:clear")

    builder.adjust(1)
    return builder.as_markup()


def get_actions_list_kb(
    actions: list[dict],
    page: int,
    total_pages: int,
    action_type: str = "edit",  # 'edit' или 'delete' или 'test'
) -> InlineKeyboardMarkup:
    """
    Генерация списка действий с пагинацией.
    action_type влияет на callback_data кнопок действий.
    """
    builder = InlineKeyboardBuilder()

    # Кнопки действий
    for action in actions:
        emoji = action["emoji"]
        name = action["name"]
        action_id = action["id"]

        # Разные callback в зависимости от цели (редактирование, удаление, тест)
        if action_type == "delete":
            cb_data = f"admin:action:del_confirm:{action_id}"
        elif action_type == "test":
            cb_data = f"admin:test:run:{action_id}"
        else:
            cb_data = f"admin:action:edit:{action_id}"

        builder.button(text=f"{emoji} {name}", callback_data=cb_data)

    builder.adjust(2)  # По 2 действия в строке

    # Кнопки навигации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"admin:action:list:{page - 1}:{action_type}",
            )
        )

    # Счетчик страниц
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore")
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"admin:action:list:{page + 1}:{action_type}",
            )
        )

    builder.row(*nav_buttons)

    # Кнопка "Назад в меню"
    builder.row(
        InlineKeyboardButton(
            text="🔙 В меню действий", callback_data="admin:actions_menu"
        )
    )

    return builder.as_markup()


def get_action_edit_kb(action_id: int) -> InlineKeyboardMarkup:
    """Меню редактирования конкретного действия"""
    builder = InlineKeyboardBuilder()

    builder.button(text="📝 Название", callback_data=f"admin:edit:{action_id}:name")
    builder.button(text="✨ Эмодзи", callback_data=f"admin:edit:{action_id}:emoji")
    builder.button(
        text="🔄 Инфинитив", callback_data=f"admin:edit:{action_id}:infinitive"
    )
    builder.button(text="🕒 Прошедшее", callback_data=f"admin:edit:{action_id}:past")
    builder.button(text="🔡 Родительный", callback_data=f"admin:edit:{action_id}:noun")

    builder.adjust(2)

    builder.row(
        InlineKeyboardButton(text="🔙 К списку", callback_data="admin:action:list:1")
    )

    return builder.as_markup()


def get_cancel_kb() -> ReplyKeyboardMarkup:
    """Кнопка отмены для FSM"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True
    )
