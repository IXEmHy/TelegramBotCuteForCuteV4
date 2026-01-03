"""
Клавиатуры для выбора и изменения пола пользователя
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ============================================================
# КЛАВИАТУРА: Выбор пола (первый раз)
# ============================================================


def get_gender_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для первичного выбора пола

    Returns:
        InlineKeyboardMarkup с кнопками выбора пола
    """
    builder = InlineKeyboardBuilder()

    # Кнопки выбора пола
    builder.row(
        InlineKeyboardButton(text="👨 Мужской", callback_data="gender:select:male"),
        InlineKeyboardButton(text="👩 Женский", callback_data="gender:select:female"),
    )

    return builder.as_markup()


# ============================================================
# КЛАВИАТУРА: Изменение пола (с подтверждением)
# ============================================================


def get_gender_change_keyboard(current_gender: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для изменения пола с показом текущего

    Args:
        current_gender: Текущий пол ('male' или 'female')

    Returns:
        InlineKeyboardMarkup с кнопками изменения
    """
    builder = InlineKeyboardBuilder()

    # Показываем противоположный пол для изменения
    if current_gender == "male":
        builder.row(
            InlineKeyboardButton(
                text="👩 Изменить на женский", callback_data="gender:change:female"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="👨 Изменить на мужской", callback_data="gender:change:male"
            )
        )

    # Кнопка отмены
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="gender:cancel"))

    return builder.as_markup()


# ============================================================
# КЛАВИАТУРА: Подтверждение изменения пола
# ============================================================


def get_gender_change_confirmation_keyboard(new_gender: str) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения изменения пола

    Args:
        new_gender: Новый выбранный пол ('male' или 'female')

    Returns:
        InlineKeyboardMarkup с кнопками подтверждения
    """
    builder = InlineKeyboardBuilder()

    # Кнопка подтверждения
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, изменить", callback_data=f"gender:confirm:{new_gender}"
        )
    )

    # Кнопка отмены
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="gender:cancel"))

    return builder.as_markup()


# ============================================================
# КЛАВИАТУРА: Настройки пола в меню
# ============================================================


def get_gender_settings_keyboard(
    current_gender: str, remaining_changes: int
) -> InlineKeyboardMarkup:
    """
    Клавиатура меню настроек пола

    Args:
        current_gender: Текущий пол ('male' или 'female')
        remaining_changes: Количество оставшихся изменений

    Returns:
        InlineKeyboardMarkup с меню настроек
    """
    builder = InlineKeyboardBuilder()

    # Показываем текущий пол
    gender_emoji = "👨" if current_gender == "male" else "👩"
    gender_text = "Мужской" if current_gender == "male" else "Женский"

    # Информация о текущем поле (некликабельная)
    builder.row(
        InlineKeyboardButton(
            text=f"{gender_emoji} Текущий: {gender_text}",
            callback_data="gender:info",
        )
    )

    # Кнопка изменения пола (если есть доступные изменения)
    if remaining_changes > 0:
        builder.row(
            InlineKeyboardButton(
                text=f"🔄 Изменить пол ({remaining_changes} осталось)",
                callback_data="gender:request_change",
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="🚫 Лимит изменений исчерпан",
                callback_data="gender:limit_reached",
            )
        )

    # Кнопка назад в главное меню
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main"))

    return builder.as_markup()


# ============================================================
# КЛАВИАТУРА: Сообщение об ограничении
# ============================================================


def get_gender_limit_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для сообщения об исчерпании лимита изменений

    Returns:
        InlineKeyboardMarkup с кнопкой возврата
    """
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main"))

    return builder.as_markup()
