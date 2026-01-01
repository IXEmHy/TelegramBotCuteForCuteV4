"""
Админские команды для управления ботом
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
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
from bot.fsm.admin_states import ActionAddStates, BroadcastStates

logger = logging.getLogger(__name__)
router = Router(name="admin")


async def is_admin(user_id: int, admin_repo: AdminRepository) -> bool:
    """Проверка прав администратора"""
    if user_id == settings.admin_id:
        return True
    return await admin_repo.is_admin(user_id)


# ============================================
# ГЛОБАЛЬНАЯ СТАТИСТИКА
# ============================================


@router.message(Command("stats_global"))
async def cmd_stats_global(
    message: Message,
    admin_repo: AdminRepository,
    action_stat_repo: ActionStatRepository,
    user_repo: UserRepository,
):
    """Глобальная статистика бота"""
    if not await is_admin(message.from_user.id, admin_repo):
        return

    # Получаем глобальную статистику
    global_stats = await action_stat_repo.get_global_stats()

    # Получаем топ-5 самых активных пользователей
    top_users = await action_stat_repo.get_top_users(limit=5)

    top_users_text = ""
    if top_users:
        for i, user_stat in enumerate(top_users, 1):
            user = await user_repo.get(user_stat["user_id"])
            username = user.username if user and user.username else "Аноним"
            top_users_text += (
                f"{i}. @{username} - {user_stat['total_actions']} действий\n"
            )
    else:
        top_users_text = "<i>Нет данных</i>"

    stats_text = (
        "<b>📊 Глобальная статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{global_stats.get('total_users', 0)}</b>\n"
        f"🔄 Всего действий: <b>{global_stats.get('total_actions', 0)}</b>\n"
        f"✅ Принято: <b>{global_stats.get('accepted', 0)}</b>\n"
        f"❌ Отклонено: <b>{global_stats.get('declined', 0)}</b>\n\n"
        "<b>🏆 Топ-5 пользователей:</b>\n"
        f"{top_users_text}"
    )

    await message.answer(stats_text, parse_mode="HTML")


# ============================================
# УПРАВЛЕНИЕ ДЕЙСТВИЯМИ
# ============================================


@router.message(Command("add_action"))
async def cmd_add_action(
    message: Message, state: FSMContext, admin_repo: AdminRepository
):
    """Начать добавление нового действия"""
    if not await is_admin(message.from_user.id, admin_repo):
        return

    await state.set_state(ActionAddStates.waiting_for_name)
    await message.answer(
        "<b>➕ Добавление нового действия</b>\n\n"
        "📝 Введите <b>название действия</b> (с большой буквы):\n"
        "Пример: <code>Обнять</code>\n\n"
        "Отправьте /cancel для отмены",
        parse_mode="HTML",
    )


@router.message(ActionAddStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка названия действия"""
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Добавление действия отменено")
        return

    await state.update_data(name=message.text.strip())
    await state.set_state(ActionAddStates.waiting_for_emoji)
    await message.answer(
        "✨ Отправьте <b>эмодзи</b> для действия:\nПример: 🤗", parse_mode="HTML"
    )


@router.message(ActionAddStates.waiting_for_emoji)
async def process_emoji(message: Message, state: FSMContext):
    """Обработка эмодзи"""
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Добавление действия отменено")
        return

    await state.update_data(emoji=message.text.strip())
    await state.set_state(ActionAddStates.waiting_for_infinitive)
    await message.answer(
        "🔄 Введите форму <b>инфинитива</b> (что сделать?):\n"
        "Пример: <code>обнять</code> (строчными буквами)",
        parse_mode="HTML",
    )


@router.message(ActionAddStates.waiting_for_infinitive)
async def process_infinitive(message: Message, state: FSMContext):
    """Обработка инфинитива"""
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Добавление действия отменено")
        return

    await state.update_data(infinitive=message.text.lower().strip())
    await state.set_state(ActionAddStates.waiting_for_past)
    await message.answer(
        "🕒 Введите форму <b>прошедшего времени</b> (что сделал?):\n"
        "Пример: <code>обнял</code>",
        parse_mode="HTML",
    )


@router.message(ActionAddStates.waiting_for_past)
async def process_past(message: Message, state: FSMContext):
    """Обработка прошедшего времени"""
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Добавление действия отменено")
        return

    await state.update_data(past_tense=message.text.lower().strip())
    await state.set_state(ActionAddStates.waiting_for_noun)
    await message.answer(
        "🔡 Введите форму <b>родительного падежа</b> (от кого/чего?):\n"
        "Пример: <code>объятия</code>\n"
        "(Используется в фразе: 'отказался от ...')",
        parse_mode="HTML",
    )


@router.message(ActionAddStates.waiting_for_noun)
async def process_noun(
    message: Message, state: FSMContext, action_repo: ActionRepository
):
    """Финальный шаг - сохранение действия"""
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Добавление действия отменено")
        return

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

        # Очищаем кэш
        cache = await get_cache_service()
        if cache:
            await cache.invalidate_actions()

        await message.answer(
            f"✅ Действие <b>{new_action.name}</b> успешно добавлено!\n\n"
            f"<b>Превью:</b>\n"
            f"{new_action.emoji} Пользователь хочет {new_action.infinitive}\n\n"
            f"Используйте /list_actions для просмотра всех действий",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error creating action: {e}", exc_info=True)
        await message.answer("❌ Ошибка при сохранении в БД")

    await state.clear()


@router.message(Command("list_actions"))
async def cmd_list_actions(
    message: Message,
    admin_repo: AdminRepository,
    action_repo: ActionRepository,
):
    """Список всех действий"""
    if not await is_admin(message.from_user.id, admin_repo):
        return

    cache = await get_cache_service()
    action_service = ActionService(action_repo, cache)
    all_actions = await action_service.get_all_actions()

    if not all_actions:
        await message.answer("📋 В базе нет действий")
        return

    # Группируем по пакам
    packs = {}
    for action in all_actions:
        pack = action.get("pack", "Без пака")
        if pack not in packs:
            packs[pack] = []
        packs[pack].append(action)

    text_parts = ["<b>📋 Список всех действий</b>\n"]

    for pack_name, actions in packs.items():
        text_parts.append(f"\n<b>{pack_name}</b> ({len(actions)}):")
        for action in actions[:10]:  # Показываем первые 10
            text_parts.append(
                f"• {action['emoji']} {action['name']} (ID: {action['id']})"
            )
        if len(actions) > 10:
            text_parts.append(f"... и ещё {len(actions) - 10}")

    text_parts.append(f"\n\n<b>Всего действий: {len(all_actions)}</b>")

    await message.answer("\n".join(text_parts), parse_mode="HTML")


# ============================================
# УПРАВЛЕНИЕ КЭШЕМ
# ============================================


@router.message(Command("cache_clear"))
async def cmd_cache_clear(
    message: Message,
    admin_repo: AdminRepository,
):
    """Очистка кэша"""
    if not await is_admin(message.from_user.id, admin_repo):
        return

    cache = await get_cache_service()
    if cache:
        await cache.invalidate_actions()
        await message.answer("✅ Кэш действий успешно очищен!")
    else:
        await message.answer("⚠️ Redis не подключен, кэш не используется")


# ============================================
# РАССЫЛКА
# ============================================


@router.message(Command("broadcast"))
async def cmd_broadcast(
    message: Message,
    state: FSMContext,
    admin_repo: AdminRepository,
):
    """Начать рассылку"""
    if not await is_admin(message.from_user.id, admin_repo):
        return

    await state.set_state(BroadcastStates.waiting_for_message)
    await message.answer(
        "<b>📢 Рассылка сообщения всем пользователям</b>\n\n"
        "Отправьте текст сообщения для рассылки.\n"
        "Можно использовать HTML-разметку.\n\n"
        "Отправьте /cancel для отмены",
        parse_mode="HTML",
    )


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast(
    message: Message,
    state: FSMContext,
    user_repo: UserRepository,
):
    """Обработка и отправка рассылки"""
    if message.text and message.text.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Рассылка отменена")
        return

    broadcast_text = message.text or message.caption or ""

    if not broadcast_text:
        await message.answer("❌ Сообщение не может быть пустым")
        return

    # Получаем всех пользователей
    all_users = await user_repo.get_all()

    if not all_users:
        await message.answer("⚠️ В базе нет пользователей для рассылки")
        await state.clear()
        return

    # Отправляем подтверждение
    confirmation = await message.answer(
        f"📤 Начинаю рассылку для {len(all_users)} пользователей..."
    )

    # Рассылка
    success_count = 0
    failed_count = 0

    for user in all_users:
        try:
            await message.bot.send_message(
                chat_id=user.telegram_id,
                text=broadcast_text,
                parse_mode="HTML",
            )
            success_count += 1
        except Exception as e:
            logger.warning(f"Failed to send to {user.telegram_id}: {e}")
            failed_count += 1

    # Итоги
    await confirmation.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"✅ Успешно: {success_count}\n"
        f"❌ Ошибок: {failed_count}\n"
        f"📊 Всего: {len(all_users)}",
        parse_mode="HTML",
    )

    await state.clear()
