"""
Обработчик inline запросов (@bot ...)

ВОЗМОЖНОСТИ:
- Топ-5 персональных действий пользователя
- Показ всех действий из стандартного пака (до 50 штук из-за лимита Telegram)
- Поиск по действиям
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
    """
    Создать inline результат для действия

    Args:
        action_data: Данные действия из БД
        sender: Отправитель (query.from_user)
        result_id: ID результата (опционально)
    """
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


async def show_favorites_and_catalog(
    query: InlineQuery,
    action_service: ActionService,
    action_stat_repo: ActionStatRepository,
):
    """
    Показать избранные действия пользователя + кнопку каталога
    """
    sender = query.from_user
    results = []

    # Получаем топ-5 действий пользователя
    top_actions = await action_stat_repo.get_user_top_actions(sender.id, limit=5)

    if top_actions:
        # Загружаем полные данные действий
        all_actions_dict = {
            action["name"]: action for action in await action_service.get_all_actions()
        }

        # Добавляем заголовок для избранных
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="⭐ Ваши любимые действия",
                description=f"Топ-{len(top_actions)} часто используемых",
                input_message_content=InputTextMessageContent(
                    message_text="💡 Выберите действие из списка ниже"
                ),
            )
        )

        # Добавляем топ-5 действий
        for top_action in top_actions:
            action_name = top_action["action_name"]
            count = top_action["count"]

            action_data = all_actions_dict.get(action_name)
            if action_data:
                result = create_action_result(action_data, sender)
                # Обновляем описание с количеством использований
                result.description = f"Использовано: {count} раз"
                results.append(result)

    # Добавляем кнопку "Показать все действия"
    results.append(
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="📋 Показать все действия",
            description="Введите 'все' для просмотра полного каталога",
            input_message_content=InputTextMessageContent(
                message_text=(
                    "💡 **Как использовать:**\n\n"
                    "Введите `@CuteForCuteBot все` для просмотра всех действий\n"
                    "или начните вводить название для поиска"
                ),
                parse_mode="Markdown",
            ),
        )
    )

    return results


async def show_all_actions(
    query: InlineQuery, action_service: ActionService
) -> list[InlineQueryResultArticle]:
    """
    Показать все действия (максимум 49 + заголовок = 50)
    """
    sender = query.from_user
    all_actions = await action_service.get_all_actions()

    total_count = len(all_actions)

    # Ограничиваем до 49 действий (+ 1 заголовок = 50 макс.)
    limited_actions = all_actions[:49]

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"📦 Все действия ({total_count} шт.)",
            description=f"Показано первых {len(limited_actions)} действий",
            input_message_content=InputTextMessageContent(
                message_text="💡 Выберите действие из списка ниже"
            ),
        )
    ]

    # Добавляем действия
    for action_data in limited_actions:
        results.append(create_action_result(action_data, sender))

    return results


async def search_actions(
    query: InlineQuery, action_service: ActionService, search_query: str
) -> list[InlineQueryResultArticle]:
    """
    Поиск действий по запросу
    """
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
            description=f"Найдено действий по запросу '{search_query}'",
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
    1. Пустой запрос → Топ-5 + кнопка "Показать все"
    2. "все" или "all" → Показать все действия (макс. 50)
    3. Любой текст → Поиск по действиям
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

        # === РЕЖИМ 1: Пустой запрос - показать избранные + каталог ===
        if not query_text:
            results = await show_favorites_and_catalog(
                query, action_service, action_stat_repo
            )

        # === РЕЖИМ 2: Запрос "все" - показать все действия ===
        elif query_text in ["все", "all", "catalog", "каталог"]:
            results = await show_all_actions(query, action_service)

        # === РЕЖИМ 3: Поиск по действиям ===
        else:
            results = await search_actions(query, action_service, query_text)

        # Отправляем результаты (максимум 50)
        await query.answer(results[:50], cache_time=5, is_personal=True)

        logger.debug(
            f"👤 {query.from_user.full_name} ({query.from_user.id}) | "
            f"Запрос: '{query_text}' | "
            f"Результатов: {len(results)}"
        )

    except Exception as e:
        logger.error(f"❌ Error inline: {e}", exc_info=True)
        # Отправляем пустой результат при ошибке
        await query.answer([], cache_time=1)
