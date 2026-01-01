"""
Обработчик inline запросов (@bot ...)

ВОЗМОЖНОСТИ:
- Топ-10 самых популярных действий (глобально)
- Поиск по действиям
- Информационное сообщение про полный список
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
)
from bot.services.cache import get_cache_service
from bot.utils.conjugator import get_short_name

router = Router(name="inline")
logger = logging.getLogger(__name__)


def create_action_result(
    action_data: dict, sender, result_id: str = None
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
        description="",
        input_message_content=InputTextMessageContent(
            message_text=message_text,
            parse_mode="Markdown",
        ),
        reply_markup=keyboard,
    )


async def get_global_top_actions(
    action_stat_repo: ActionStatRepository,
    action_service: ActionService,
    limit: int = 10,
) -> list[dict]:
    """
    Получить топ-N самых популярных действий глобально

    Returns:
        list[dict]: Список действий с их данными
    """
    from sqlalchemy import select, func
    from bot.database.models import Interaction

    # Получаем топ действий по количеству использований
    query = (
        select(Interaction.action, func.count(Interaction.id).label("count"))
        .group_by(Interaction.action)
        .order_by(func.count(Interaction.id).desc())
        .limit(limit)
    )

    result = await action_stat_repo.session.execute(query)
    top_actions_data = result.all()

    # Загружаем полные данные действий
    all_actions_dict = {
        action["name"]: action for action in await action_service.get_all_actions()
    }

    top_actions = []
    for action_name, count in top_actions_data:
        action_data = all_actions_dict.get(action_name)
        if action_data:
            action_data["usage_count"] = count
            top_actions.append(action_data)

    return top_actions


async def show_popular_and_info(
    query: InlineQuery,
    action_service: ActionService,
    action_stat_repo: ActionStatRepository,
):
    """
    Показать топ-10 популярных действий + информационное сообщение
    """
    sender = query.from_user
    results = []

    # Получаем топ-10 популярных действий глобально
    try:
        top_actions = await get_global_top_actions(
            action_stat_repo, action_service, limit=10
        )
    except Exception as e:
        logger.warning(f"⚠️ Не удалось загрузить популярные действия: {e}")
        # Если нет статистики - показываем первые 10 действий
        all_actions = await action_service.get_all_actions()
        top_actions = all_actions[:10]

    if top_actions:
        # Добавляем заголовок
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="🔥 Самые популярные действия",
                description=f"Топ-{len(top_actions)} действий среди всех пользователей",
                input_message_content=InputTextMessageContent(
                    message_text="💡 Выберите действие из списка ниже"
                ),
            )
        )

        # Добавляем популярные действия
        for action_data in top_actions:
            result = create_action_result(action_data, sender)
            # Если есть статистика - показываем
            if "usage_count" in action_data:
                result.description = f"Использовано: {action_data['usage_count']} раз"
            results.append(result)

    # Добавляем информационное сообщение про полный список
    results.append(
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="📋 Полный список действий",
            description="Как посмотреть все доступные действия",
            input_message_content=InputTextMessageContent(
                message_text=(
                    "📋 **Все доступные действия:**\n\n"
                    "Всего доступно 65+ действий!\n\n"
                    "**Как найти нужное:**\n"
                    "• Начните вводить название (например: `обн`, `поц`, `уд`)\n"
                    "• Бот покажет все подходящие варианты\n\n"
                    "💡 **Совет:** Используйте поиск для быстрого доступа к нужному действию!"
                ),
                parse_mode="Markdown",
            ),
        )
    )

    return results


async def search_actions(
    query: InlineQuery, action_service: ActionService, search_query: str
) -> list[InlineQueryResultArticle]:
    """Поиск действий по запросу"""
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

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"🔍 Результаты поиска: {len(found_actions)}",
            description=f"Найдено по запросу '{search_query}'",
            input_message_content=InputTextMessageContent(
                message_text="💡 Выберите действие из результатов поиска"
            ),
        )
    ]

    # Ограничиваем до 49 (50 - заголовок)
    for action_data in found_actions[:49]:
        results.append(create_action_result(action_data, sender))

    return results


@router.inline_query()
async def inline_query_handler(
    query: InlineQuery,
    user_repo: UserRepository,
    action_repo: ActionRepository,
    action_stat_repo: ActionStatRepository,
):
    """
    Главный обработчик inline запросов

    ЛОГИКА:
    1. Пустой запрос → Топ-10 популярных + инфо про полный список
    2. Любой текст → Поиск по действиям
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

        # === РЕЖИМ 1: Пустой запрос - показать популярные + инфо ===
        if not query_text:
            results = await show_popular_and_info(
                query, action_service, action_stat_repo
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
