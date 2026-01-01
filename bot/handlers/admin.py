"""
Админ-панель для управления ботом
"""

import logging
import math

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from bot.core.config import settings
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
    get_cancel_kb,
)
from bot.fsm.admin_states import ActionAddStates

logger = logging.getLogger(__name__)
router = Router(name="admin")

PAGE_SIZE = 10


async def is_admin(user_id: int, admin_repo: AdminRepository) -> bool:
    """Проверка прав администратора"""
    if user_id == settings.admin_id:
        return True
    return await admin_repo.is_admin(user_id)


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
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("admin:action:list:"))
async def show_actions_list(
    callback: CallbackQuery, action_repo: ActionRepository, admin_repo: AdminRepository
):
    """Показать список действий с пагинацией"""
    if not await is_admin(callback.from_user.id, admin_repo):
        return

    parts = callback.data.split(":")
    page = int(parts[3])
    action_type = parts[4] if len(parts) > 4 else "edit"

    cache = await get_cache_service()
    action_service = ActionService(action_repo, cache)

    all_actions = await action_service.get_all_actions()

    total_actions = len(all_actions)
    total_pages = math.ceil(total_actions / PAGE_SIZE) if total_actions > 0 else 1

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
    await callback.answer()


@router.callback_query(F.data.startswith("admin:action:delete_list:"))
async def delete_mode_proxy(
    callback: CallbackQuery, action_repo: ActionRepository, admin_repo: AdminRepository
):
    """Переходник для режима удаления"""
    callback.data = "admin:action:list:1:delete"
    await show_actions_list(callback, action_repo, admin_repo)


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
    """Обработка названия действия"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=get_admin_menu())
        return

    await state.update_data(name=message.text.strip())
    await state.set_state(ActionAddStates.waiting_for_emoji)
    await message.answer("✨ Отправьте **эмодзи** для действия:")


@router.message(ActionAddStates.waiting_for_emoji)
async def process_emoji(message: Message, state: FSMContext):
    """Обработка эмодзи"""
    await state.update_data(emoji=message.text.strip())
    await state.set_state(ActionAddStates.waiting_for_infinitive)
    await message.answer(
        "🔄 Введите форму **инфинитива** (что сделать?):\nПример: `обнять` (строчными)",
        parse_mode="Markdown",
    )


@router.message(ActionAddStates.waiting_for_infinitive)
async def process_infinitive(message: Message, state: FSMContext):
    """Обработка инфинитива"""
    await state.update_data(infinitive=message.text.lower().strip())
    await state.set_state(ActionAddStates.waiting_for_past)
    await message.answer(
        "🕒 Введите форму **прошедшего времени** (что сделал?):\nПример: `обнял`",
        parse_mode="Markdown",
    )


@router.message(ActionAddStates.waiting_for_past)
async def process_past(message: Message, state: FSMContext):
    """Обработка прошедшего времени"""
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
    """Финальный шаг - сохранение действия"""
    data = await state.get_data()
    genitive_noun = message.text.lower().strip()

    try:
        new_action = await action_repo.create(
            name=data["name"],
            emoji=data["emoji"],
            infinitive=data["infinitive"],
            past_tense=data["past_tense"],
            genitive_noun=genitive_noun,
        )

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
        logger.error(f"Error creating action: {e}", exc_info=True)
        await message.answer("❌ Ошибка при сохранении в БД.")

    await state.clear()


@router.callback_query(lambda c: c.data.startswith("admin:action:del_confirm:"))
async def delete_action_confirm(callback: CallbackQuery, action_repo: ActionRepository):
    """Подтверждение удаления действия"""
    action_id = int(callback.data.split(":")[-1])

    if await action_repo.delete(action_id):
        cache = await get_cache_service()
        if cache:
            await cache.invalidate_actions()

        await callback.answer("✅ Действие удалено!", show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
    else:
        await callback.answer("❌ Ошибка удаления", show_alert=True)


@router.callback_query(F.data == "admin:cache:clear")
async def clear_cache(callback: CallbackQuery):
    """Очистка кэша"""
    cache = await get_cache_service()
    if cache:
        await cache.invalidate_actions()
        await callback.answer("✅ Кэш очищен!", show_alert=True)
    else:
        await callback.answer("⚠️ Redis не подключен", show_alert=True)


@router.message(F.text == "👥 Статистика")
async def admin_stats(
    message: Message,
    action_stat_repo: ActionStatRepository,
    admin_repo: AdminRepository,
):
    """Показать общую статистику бота"""
    if not await is_admin(message.from_user.id, admin_repo):
        return

    global_stats = await action_stat_repo.get_global_stats()

    await message.answer(
        "📊 **Глобальная статистика:**\n\n"
        f"👥 Всего активных пользователей: `{global_stats['total_users']}`\n"
        f"🔄 Всего совершено действий: `{global_stats['total_actions']}`\n",
        parse_mode="Markdown",
    )


@router.message(F.text == "🧪 Тест команд")
async def admin_test(message: Message, admin_repo: AdminRepository):
    """Меню тестирования"""
    if not await is_admin(message.from_user.id, admin_repo):
        return

    await message.answer(
        "🧪 **Тестовый режим**\n\nВыберите действие из меню управления для теста.",
        reply_markup=get_actions_management_menu(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    """Игнорировать callback (для счётчика страниц)"""
    await callback.answer()
