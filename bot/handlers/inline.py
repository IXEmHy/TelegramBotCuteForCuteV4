"""
Обработчик inline запросов (@bot ...)

ЛОГИКА:
- Топ-3 самых часто используемых действия пользователя
- Если меньше 3 - дополняется из стандартного пака
- Поиск без заголовка
"""

import logging
from uuid import uuid4
from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.services.user import UserService
from bot.services.action import ActionService
from bot.database.repositories import (
    UserRepository,
    ActionRepository,
    ActionStatRepository,
    InteractionRepository,
)
from bot.services.cache import get_cache_service
from bot.utils.conjugator import get_short_name

router = Router(name="inline")
logger = logging.getLogger(__name__)


def create_action_result(
    action_data: dict, sender, result_id: str = None, description: str = ""
) -> InlineQueryResultArticle:
    """Создать inline результат для действия"""
    action_id = action_data["id"]
    action_name = action_data["name"]
    emoji = action_data["emoji"]
    infinitive = action_data["infinitive"]

    # Формируем callback data
    accept_data = f"iact:{sender.id}:{action_id}:1"
    decline_data = f"iact:{sender.id}:{action_id}:0"

    # Клавиатура
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=accept_data),
                InlineKeyboardButton(text="❌ Отказаться", callback_data=decline_data),
            ]
        ]
    )

    # Текст сообщения
    sender_link = f"[{sender.full_name}](tg://user?id={sender.id})"
    message_text = f"{emoji} {sender_link} хочет {infinitive} вами"

    # Краткое название для списка
    display_name = get_short_name(action_name)

    return InlineQueryResultArticle(
        id=result_id or str(uuid4()),
        title=f"{emoji} {display_name}",
        description=description,
        input_message_content=InputTextMessageContent(
            message_text=message_text,
            parse_mode="Markdown",
        ),
        reply_markup=keyboard,
    )


async def get_user_most_used_actions(
    user_id: int,
    interaction_repo: InteractionRepository,
    action_service: ActionService,
    limit: int = 3,
) -> list[dict]:
    """
    Получить топ-N самых часто используемых действий КОНКРЕТНОГО пользователя

    Args:
        user_id: ID пользователя
        interaction_repo: Репозиторий взаимодействий
        action_service: Сервис действий
        limit: Количество действий

    Returns:
        list[dict]: Список самых часто используемых действий
    """
    from sqlalchemy import select, func
    from bot.database.models import Interaction

    # Получаем топ действий пользователя по количеству использований
    query = (
        select(Interaction.action, func.count(Interaction.id).label("usage_count"))
        .where(Interaction.sender_id == user_id)
        .group_by(Interaction.action)
        .order_by(func.count(Interaction.id).desc())
        .limit(limit)
    )

    result = await interaction_repo.session.execute(query)
    most_used_actions_data = result.all()

    if not most_used_actions_data:
        return []

    # Загружаем полные данные действий
    all_actions_dict = {
        action["name"]: action for action in await action_service.get_all_actions()
    }

    most_used_actions = []
    for action_name, usage_count in most_used_actions_data:
        action_data = all_actions_dict.get(action_name)
        if action_data:
            most_used_actions.append(action_data)

    return most_used_actions


async def show_user_top_actions(
    query: InlineQuery,
    action_service: ActionService,
    interaction_repo: InteractionRepository,
):
    """
    Показать топ-3 самых используемых действия пользователя.
    Если меньше 3 - дополнить из стандартного пака.
    """
    sender = query.from_user
    results = []

    # Получаем топ-3 самых используемых действия ЭТОГО пользователя
    try:
        top_actions = await get_user_most_used_actions(
            user_id=sender.id,
            interaction_repo=interaction_repo,
            action_service=action_service,
            limit=3,
        )
    except Exception as e:
        logger.warning(f"⚠️ Не удалось загрузить топ действия: {e}")
        top_actions = []

    # Если меньше 3 действий - дополняем из стандартного пака
    if len(top_actions) < 3:
        all_actions = await action_service.get_all_actions()

        # Получаем названия уже добавленных действий
        used_action_names = {action["name"] for action in top_actions}

        # Добавляем недостающие из начала списка
        for action in all_actions:
            if action["name"] not in used_action_names:
                top_actions.append(action)
                if len(top_actions) >= 3:
                    break

    # Описания для каждого действия
    descriptions = [
        "Эти действия вы использовали чаще всего",
        "Чтобы выбрать нужное действие начните вводить название действия",
        "Чтобы увидеть полный список доступных вам действий перейдите в ЛС бота",
    ]

    # Добавляем топ действия с описаниями (гарантированно 3 штуки)
    for idx, action_data in enumerate(top_actions[:3]):
        description = descriptions[idx] if idx < len(descriptions) else ""
        result = create_action_result(action_data, sender, description=description)
        results.append(result)

    return results


async def search_actions(
    query: InlineQuery, action_service: ActionService, search_query: str
) -> list[InlineQueryResultArticle]:
    """Поиск действий по запросу (без заголовка)"""
    sender = query.from_user
    found_actions = await action_service.search_actions(search_query)

    if not found_actions:
        return [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="❌ Ничего не найдено",
                description=f"По запросу '{search_query}' ничего не найдено",
                input_message_content=InputTextMessageContent(
                    message_text=f"Действие '{search_query}' не найдено. Попробуйте другой запрос."
                ),
            )
        ]

    # БЕЗ заголовка "Результаты поиска" - сразу показываем действия
    results = []

    # Ограничиваем до 50 результатов
    for action_data in found_actions[:50]:
        results.append(create_action_result(action_data, sender))

    return results


@router.inline_query()
async def inline_query_handler(
    query: InlineQuery,
    user_repo: UserRepository,
    action_repo: ActionRepository,
    action_stat_repo: ActionStatRepository,
    interaction_repo: InteractionRepository,
):
    """
    Главный обработчик inline запросов

    ЛОГИКА:
    1. Пустой запрос → Топ-3 действия пользователя (дополненные до 3)
    2. Любой текст → Поиск по действиям (без заголовка)
    """
    try:
        # Регистрируем пользователя
        user_service = UserService(user_repo)
        await user_service.register_or_update_user(query.from_user)

        # Получаем сервисы
        cache = await get_cache_service()
        action_service = ActionService(action_repo, cache, action_stat_repo)

        # Получаем запрос пользователя
        query_text = query.query.lower().strip()

        # === РЕЖИМ 1: Пустой запрос - показать топ действия ===
        if not query_text:
            results = await show_user_top_actions(
                query, action_service, interaction_repo
            )

        # === РЕЖИМ 2: Поиск по действиям ===
        else:
            results = await search_actions(query, action_service, query_text)

        # Отправляем результаты (строго ограничиваем до 50)
        results_to_send = results[:50]
        await query.answer(results_to_send, cache_time=5, is_personal=True)

        logger.debug(
            f"👤 {query.from_user.full_name} ({query.from_user.id}) | "
            f"Запрос: '{query_text}' | "
            f"Результатов: {len(results_to_send)}"
        )

    except Exception as e:
        logger.error(f"❌ Error inline: {e}", exc_info=True)
        # Отправляем пустой результат при ошибке
        await query.answer([], cache_time=1)
