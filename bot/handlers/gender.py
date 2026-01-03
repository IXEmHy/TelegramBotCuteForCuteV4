"""
Обработчики для выбора и изменения пола пользователя
"""

import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.orm import Session

from bot.database.models import User, GenderType
from bot.fsm.gender_states import GenderSelectionStates
from bot.keyboards.gender import (
    get_gender_selection_keyboard,
    get_gender_change_keyboard,
    get_gender_change_confirmation_keyboard,
    get_gender_settings_keyboard,
    get_gender_limit_keyboard,
)
from bot.services.user_service import UserService

logger = logging.getLogger(__name__)
router = Router(name="gender_router")


# ============================================================
# УТИЛИТЫ
# ============================================================


def get_gender_emoji(gender: str) -> str:
    """Получить emoji для пола"""
    return "👨" if gender == "male" else "👩"


def get_gender_text(gender: str) -> str:
    """Получить текстовое название пола"""
    return "Мужской" if gender == "male" else "Женский"


# ============================================================
# КОМАНДА: /gender - Управление полом
# ============================================================


@router.message(Command("gender"))
async def cmd_gender_settings(message: Message, session: Session, state: FSMContext):
    """
    Команда для просмотра и изменения пола

    Args:
        message: Сообщение от пользователя
        session: Сессия БД
        state: FSM контекст
    """
    user_id = message.from_user.id

    # Получаем пользователя
    user = session.query(User).filter(User.user_id == user_id).first()

    if not user:
        await message.answer(
            "❌ Ошибка: пользователь не найден.\nИспользуйте /start для регистрации."
        )
        return

    # Если пол не установлен - показываем выбор
    if user.gender is None:
        await show_gender_selection(message, state)
        return

    # Показываем настройки пола
    remaining = user.remaining_gender_changes

    gender_emoji = get_gender_emoji(user.gender_value)
    gender_text = get_gender_text(user.gender_value)

    text = f"""
⚙️ <b>Настройки пола</b>

{gender_emoji} <b>Текущий пол:</b> {gender_text}

📊 <b>Изменений осталось:</b> {remaining} из 3
⏰ <b>Обновление лимита:</b> каждые 30 дней

<i>Пол влияет на правильное склонение действий в боте.</i>
"""

    await message.answer(
        text,
        reply_markup=get_gender_settings_keyboard(user.gender_value, remaining),
    )


# ============================================================
# ПЕРВИЧНЫЙ ВЫБОР ПОЛА (при регистрации)
# ============================================================


async def show_gender_selection(message: Message, state: FSMContext):
    """
    Показать выбор пола новому пользователю

    Args:
        message: Сообщение от пользователя
        state: FSM контекст
    """
    text = """
👋 <b>Добро пожаловать!</b>

Для корректной работы бота выберите ваш пол.
Это нужно для правильного склонения действий.

<i>Например:</i>
• Мужской: "<b>обнял</b>, <b>поцеловал</b>"
• Женский: "<b>обняла</b>, <b>поцеловала</b>"

Вы сможете изменить пол позже (до 3 раз в месяц).
"""

    await state.set_state(GenderSelectionStates.choosing_gender)

    await message.answer(text, reply_markup=get_gender_selection_keyboard())


# ============================================================
# CALLBACK: Выбор пола (первый раз)
# ============================================================


@router.callback_query(F.data.startswith("gender:select:"))
async def callback_select_gender(
    callback: CallbackQuery, session: Session, state: FSMContext
):
    """
    Обработка выбора пола при первой регистрации

    Args:
        callback: Callback от inline-кнопки
        session: Сессия БД
        state: FSM контекст
    """
    await callback.answer()

    # Парсим выбранный пол
    _, _, gender = callback.data.split(":")

    if gender not in ["male", "female"]:
        await callback.message.edit_text("❌ Ошибка: неверный пол.")
        return

    user_id = callback.from_user.id

    # Получаем или создаём пользователя
    user = UserService.get_or_create_user(
        session=session,
        user_id=user_id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name or "User",
    )

    # Устанавливаем пол
    success = UserService.set_gender(
        session=session, user_id=user_id, gender=gender, is_first_time=True
    )

    if success:
        gender_emoji = get_gender_emoji(gender)
        gender_text = get_gender_text(gender)

        await callback.message.edit_text(
            f"""
✅ <b>Отлично!</b>

{gender_emoji} Ваш пол установлен: <b>{gender_text}</b>

Теперь все действия будут правильно склоняться.
Вы можете изменить пол до 3 раз в месяц через /gender.

Используйте /help чтобы узнать как работает бот!
"""
        )

        # Очищаем состояние
        await state.clear()

        logger.info(f"✅ User {user_id} выбрал пол: {gender}")

    else:
        await callback.message.edit_text(
            "❌ Ошибка при установке пола. Попробуйте позже."
        )


# ============================================================
# CALLBACK: Запрос изменения пола
# ============================================================


@router.callback_query(F.data == "gender:request_change")
async def callback_request_gender_change(callback: CallbackQuery, session: Session):
    """
    Запрос на изменение пола

    Args:
        callback: Callback от inline-кнопки
        session: Сессия БД
    """
    await callback.answer()

    user_id = callback.from_user.id
    user = session.query(User).filter(User.user_id == user_id).first()

    if not user:
        await callback.message.edit_text("❌ Пользователь не найден.")
        return

    # Проверяем возможность изменения
    if not user.can_change_gender:
        remaining_days = 30
        if user.last_gender_change:
            days_passed = (datetime.utcnow() - user.last_gender_change).days
            remaining_days = max(0, 30 - days_passed)

        await callback.message.edit_text(
            f"""
🚫 <b>Лимит изменений исчерпан</b>

Вы уже изменили пол {user.gender_changes_count} раза за последние 30 дней.

⏰ <b>Лимит обновится через:</b> {remaining_days} дней

<i>Лимит: 3 изменения в месяц</i>
""",
            reply_markup=get_gender_limit_keyboard(),
        )
        return

    # Показываем выбор нового пола
    current_gender = user.gender_value
    remaining = user.remaining_gender_changes

    text = f"""
🔄 <b>Изменение пола</b>

📊 <b>Осталось изменений:</b> {remaining} из 3

Выберите новый пол:
"""

    await callback.message.edit_text(
        text, reply_markup=get_gender_change_keyboard(current_gender)
    )


# ============================================================
# CALLBACK: Изменение пола
# ============================================================


@router.callback_query(F.data.startswith("gender:change:"))
async def callback_change_gender(callback: CallbackQuery, session: Session):
    """
    Обработка запроса на изменение пола

    Args:
        callback: Callback от inline-кнопки
        session: Сессия БД
    """
    await callback.answer()

    # Парсим новый пол
    _, _, new_gender = callback.data.split(":")

    if new_gender not in ["male", "female"]:
        await callback.message.edit_text("❌ Ошибка: неверный пол.")
        return

    user_id = callback.from_user.id
    user = session.query(User).filter(User.user_id == user_id).first()

    if not user:
        await callback.message.edit_text("❌ Пользователь не найден.")
        return

    # Проверяем лимит
    if not user.can_change_gender:
        await callback.message.edit_text(
            "❌ Лимит изменений исчерпан. Попробуйте позже."
        )
        return

    # Показываем подтверждение
    new_gender_emoji = get_gender_emoji(new_gender)
    new_gender_text = get_gender_text(new_gender)

    remaining = user.remaining_gender_changes - 1  # После изменения

    text = f"""
⚠️ <b>Подтверждение изменения</b>

{new_gender_emoji} <b>Новый пол:</b> {new_gender_text}

После изменения у вас останется:
📊 <b>{remaining}</b> из 3 изменений

Вы уверены?
"""

    await callback.message.edit_text(
        text, reply_markup=get_gender_change_confirmation_keyboard(new_gender)
    )


# ============================================================
# CALLBACK: Подтверждение изменения пола
# ============================================================


@router.callback_query(F.data.startswith("gender:confirm:"))
async def callback_confirm_gender_change(callback: CallbackQuery, session: Session):
    """
    Подтверждение и применение изменения пола

    Args:
        callback: Callback от inline-кнопки
        session: Сессия БД
    """
    await callback.answer()

    # Парсим новый пол
    _, _, new_gender = callback.data.split(":")

    if new_gender not in ["male", "female"]:
        await callback.message.edit_text("❌ Ошибка: неверный пол.")
        return

    user_id = callback.from_user.id

    # Применяем изменение
    success = UserService.set_gender(
        session=session, user_id=user_id, gender=new_gender, is_first_time=False
    )

    if success:
        user = session.query(User).filter(User.user_id == user_id).first()
        remaining = user.remaining_gender_changes

        new_gender_emoji = get_gender_emoji(new_gender)
        new_gender_text = get_gender_text(new_gender)

        await callback.message.edit_text(
            f"""
✅ <b>Пол успешно изменён!</b>

{new_gender_emoji} <b>Новый пол:</b> {new_gender_text}

📊 <b>Осталось изменений:</b> {remaining} из 3
⏰ <b>Лимит обновится через:</b> 30 дней

Теперь все действия будут склоняться правильно!
"""
        )

        logger.info(f"✅ User {user_id} изменил пол на: {new_gender}")

    else:
        await callback.message.edit_text(
            "❌ Не удалось изменить пол. Возможно, лимит исчерпан."
        )


# ============================================================
# CALLBACK: Отмена
# ============================================================


@router.callback_query(F.data == "gender:cancel")
async def callback_cancel_gender_action(callback: CallbackQuery, state: FSMContext):
    """
    Отмена действия с полом

    Args:
        callback: Callback от inline-кнопки
        state: FSM контекст
    """
    await callback.answer("Отменено")

    await callback.message.edit_text(
        "❌ Действие отменено.\n\nИспользуйте /gender для настройки пола."
    )

    await state.clear()


# ============================================================
# CALLBACK: Информация о поле (некликабельная кнопка)
# ============================================================


@router.callback_query(F.data == "gender:info")
async def callback_gender_info(callback: CallbackQuery):
    """Заглушка для информационной кнопки"""
    await callback.answer("Это ваш текущий пол", show_alert=False)


# ============================================================
# CALLBACK: Лимит исчерпан
# ============================================================


@router.callback_query(F.data == "gender:limit_reached")
async def callback_gender_limit_reached(callback: CallbackQuery, session: Session):
    """
    Обработка нажатия на кнопку исчерпанного лимита

    Args:
        callback: Callback от inline-кнопки
        session: Сессия БД
    """
    user_id = callback.from_user.id
    user = session.query(User).filter(User.user_id == user_id).first()

    if not user or not user.last_gender_change:
        await callback.answer("Информация недоступна")
        return

    days_passed = (datetime.utcnow() - user.last_gender_change).days
    remaining_days = max(0, 30 - days_passed)

    await callback.answer(
        f"Лимит обновится через {remaining_days} дней", show_alert=True
    )
