"""
Админ-панель для управления ботом
"""

import logging
import math
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from bot.core.config import settings
from bot.database.models import Action
from bot.database.repositories import (
    UserRepository,
    ActionRepository,
    ActionStatRepository,
    AdminRepository,
)
from bot.services.action import ActionService
from bot.services.cache import get_cache_service
from bot.keyboards.admin_kb import (
    get_admin_menu,
    get_actions_management_menu,
    get_actions_list_kb,
    get_action_edit_kb,
    get_cancel_kb,
)
from bot.fsm.admin_states import ActionAddStates, ActionEditStates

logger = logging.getLogger(__name__)
router = Router(name="admin")

# Количество действий на одной странице
PAGE_SIZE = 10


# ==================== ПРОВЕРКИ ====================


async def is_admin(user_id: int, admin_repo: AdminRepository) -> bool:
    """Проверка прав администратора"""
    # Хардкод проверка из config (для главного админа)
    if user_id == settings.admin_id:
        return True
    # Проверка из БД
    return await admin_repo.is_admin(user_id)


# ==================== БАЗОВЫЕ КОМАНДЫ ====================


@router.message(Command("admin"))
async def admin_start(message: Message, admin_repo: AdminRepository):
    """Вход в админ-панель"""
    if not await is_admin(message.from_user.id, admin_repo):
        return

    await message.answer(
        "👋 Добро пожаловать в админ-панель!", reply_markup=get_admin_menu()
    )


@router.message(F.text == "⬅️ Выйти")
async def admin_exit(message: Message, admin_repo: AdminRepository):
    """Выход из админ-панели"""
    if not await is_admin(message.from_user.id, admin_repo):
        return

    await message.answer(
        "Вы вышли из режима администратора.", reply_markup=ReplyKeyboardRemove()
    )


# ==================== УПРАВЛЕНИЕ ДЕЙСТВИЯМИ ====================


@router.message(F.text == "🔧 Управление действиями")
async def manage_actions_menu(message: Message, admin_repo: AdminRepository):
    """Меню управления действиями"""
    if not await is_admin(message.from_user.id, admin_repo):
        return

    await message.answer(
        "🔧 **Управление действиями**\n\n"
        "Здесь вы можете добавлять, редактировать и удалять действия.",
        reply_markup=get_actions_management_menu(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "admin:actions_menu")
async def back_to_actions_menu(callback: CallbackQuery):
    """Возврат в меню действий"""
    await callback.message.edit_text(
        "🔧 **Управление действиями**",
        reply_markup=get_actions_management_menu(),
        parse_mode="Markdown",
    )


# ==================== ПРОСМОТР СПИСКА (ПАГИНАЦИЯ) ====================


@router.callback_query(lambda c: c.data.startswith("admin:action:list:"))
async def show_actions_list(
    callback: CallbackQuery, action_repo: ActionRepository, admin_repo: AdminRepository
):
    """Показать список действий с пагинацией"""
    if not await is_admin(callback.from_user.id, admin_repo):
        return

    # Парсинг данных: admin:action:list:{page}:{type}
    parts = callback.data.split(":")
    page = int(parts[3])
    # Если тип не передан, считаем 'edit'
    action_type = parts[4] if len(parts) > 4 else "edit"

    # Получаем сервис
    cache = await get_cache_service()
    action_service = ActionService(action_repo, cache)

    # Получаем все действия
    all_actions = await action_service.get_all_actions()

    # Пагинация
    total_actions = len(all_actions)
    total_pages = math.ceil(total_actions / PAGE_SIZE)

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    current_actions = all_actions[start:end]

    title = "✏️ Выберите действие для редактирования:"
    if action_type == "delete":
        title = "🗑 Выберите действие для удаления:"
    elif action_type == "test":
        title = "🧪 Выберите действие для теста:"

    await callback.message.edit_text(
        f"{title}\nСтраница {page} из {total_pages} (Всего: {total_actions})",
        reply_markup=get_actions_list_kb(
            current_actions, page, total_pages, action_type
        ),
    )


@router.callback_query(F.data.startswith("admin:action:delete_list:"))
async def delete_list_start(callback: CallbackQuery):
    """Переход в режим удаления (первая страница)"""
    # Проксируем вызов в show_actions_list с типом 'delete'
    # Подменяем data чтобы хэндлер выше его поймал
    callback.data = "admin:action:list:1:delete"
    # Нам нужно вызвать функцию напрямую или через диспетчер,
    # но проще просто изменить data и пусть роутер разберется,
    # однако в aiogram так нельзя "перевызвать".
    # Поэтому просто дублируем логику вызова (или вызываем функцию, передав аргументы)
    # НО так как мы в асинхронной среде, лучше просто сделать отдельный хэндлер или
    # явно вызвать show_actions_list.
    # ДЛЯ ПРОСТОТЫ: я изменил callback.data в декораторе выше (startswith),
    # поэтому просто скорректируйте вызов в кнопке меню (см. admin_kb.py).
    pass
    # Примечание: в admin_kb.py я уже поставил callback_data="admin:action:delete_list:1"
    # Мы сделаем отдельный хэндлер-переходник:


@router.callback_query(F.data.startswith("admin:action:delete_list:"))
async def delete_mode_proxy(
    callback: CallbackQuery, action_repo: ActionRepository, admin_repo: AdminRepository
):
    """Переходник для режима удаления"""
    # Меняем data для логики пагинации
    callback.data = "admin:action:list:1:delete"
    await show_actions_list(callback, action_repo, admin_repo)


# ==================== ДОБАВЛЕНИЕ ДЕЙСТВИЯ (FSM) ====================


@router.callback_query(F.data == "admin:action:add")
async def start_add_action(callback: CallbackQuery, state: FSMContext):
    """Начало добавления действия"""
    await state.set_state(ActionAddStates.waiting_for_name)
    await callback.message.answer(
        "📝 Введите **название действия** (с большой буквы):\nПример: `Обнять`",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ActionAddStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=get_admin_menu())
        return

    await state.update_data(name=message.text.strip())
    await state.set_state(ActionAddStates.waiting_for_emoji)
    await message.answer("✨ Отправьте **эмодзи** для действия:")


@router.message(ActionAddStates.waiting_for_emoji)
async def process_emoji(message: Message, state: FSMContext):
    await state.update_data(emoji=message.text.strip())
    await state.set_state(ActionAddStates.waiting_for_infinitive)
    await message.answer(
        "🔄 Введите форму **инфинитива** (что сделать?):\nПример: `обнять` (строчными)",
        parse_mode="Markdown",
    )


@router.message(ActionAddStates.waiting_for_infinitive)
async def process_infinitive(message: Message, state: FSMContext):
    await state.update_data(infinitive=message.text.lower().strip())
    await state.set_state(ActionAddStates.waiting_for_past)
    await message.answer(
        "🕒 Введите форму **прошедшего времени** (что сделал?):\nПример: `обнял`",
        parse_mode="Markdown",
    )


@router.message(ActionAddStates.waiting_for_past)
async def process_past(message: Message, state: FSMContext):
    await state.update_data(past_tense=message.text.lower().strip())
    await state.set_state(ActionAddStates.waiting_for_noun)
    await message.answer(
        "🔡 Введите форму **родительного падежа** (от кого/чего?):\n"
        "Пример: `объятия`\n"
        "(Используется в фразе: 'отказался от ...')",
        parse_mode="Markdown",
    )


@router.message(ActionAddStates.waiting_for_noun)
async def process_noun(
    message: Message, state: FSMContext, action_repo: ActionRepository
):
    data = await state.get_data()
    genitive_noun = message.text.lower().strip()

    # Сохраняем в БД
    try:
        new_action = await action_repo.create(
            name=data["name"],
            emoji=data["emoji"],
            infinitive=data["infinitive"],
            past_tense=data["past_tense"],
            genitive_noun=genitive_noun,
        )

        # Очищаем кэш
        cache = await get_cache_service()
        if cache:
            await cache.invalidate_actions()

        await message.answer(
            f"✅ Действие **{new_action.name}** успешно добавлено!\n\n"
            f"Тест: {new_action.emoji} User хочет {new_action.infinitive}",
            reply_markup=get_admin_menu(),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Error creating action: {e}")
        await message.answer("❌ Ошибка при сохранении в БД.")

    await state.clear()


# ==================== УДАЛЕНИЕ ДЕЙСТВИЯ ====================


@router.callback_query(lambda c: c.data.startswith("admin:action:del_confirm:"))
async def delete_action_confirm(callback: CallbackQuery, action_repo: ActionRepository):
    action_id = int(callback.data.split(":")[-1])

    if await action_repo.delete(action_id):
        # Очищаем кэш
        cache = await get_cache_service()
        if cache:
            await cache.invalidate_actions()

        await callback.answer("✅ Действие удалено!", show_alert=True)
        # Обновляем список (возвращаемся на 1 страницу)
        callback.data = "admin:action:list:1:delete"
        # Вызываем логику показа (но здесь проще просто отправить новое сообщение или эмулировать)
        # Для простоты просто удалим сообщение
        await callback.message.delete()
        await callback.message.answer("🗑 Действие удалено.")
    else:
        await callback.answer("❌ Ошибка удаления", show_alert=True)


# ==================== КЭШ ====================


@router.callback_query(F.data == "admin:cache:clear")
async def clear_cache(callback: CallbackQuery):
    cache = await get_cache_service()
    if cache:
        await cache.invalidate_actions()
        await callback.answer("✅ Кэш очищен!", show_alert=True)
    else:
        await callback.answer("⚠️ Redis не подключен", show_alert=True)
