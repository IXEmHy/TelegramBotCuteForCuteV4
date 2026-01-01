"""
Обработчик inline запросов (@bot ...)

ИЗМЕНЕНИЯ:
- Загрузка действий из БД вместо config.py
- Использование ActionService с кэшированием
- Запись статистики использования
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


@router.inline_query()
async def inline_query_handler(
    query: InlineQuery,
    user_repo: UserRepository,
    action_repo: ActionRepository,
    action_stat_repo: ActionStatRepository,
):
    """
    Обработка инлайн запросов.

    РАБОТА:
    1. Регистрирует пользователя
    2. Загружает действия из БД (через кэш)
    3. Фильтрует по запросу пользователя
    4. Формирует inline-результаты
    """
    try:
        # Регистрируем пользователя
        user_service = UserService(user_repo)
        await user_service.register_or_update_user(query.from_user)

        # Получаем сервис действий
        cache = await get_cache_service()
        action_service = ActionService(action_repo, cache, action_stat_repo)

        # Загружаем все действия
        query_text = query.query.lower().strip()

        if query_text:
            # Если есть поисковый запрос - ищем
            all_actions = await action_service.search_actions(query_text)
        else:
            # Иначе показываем все
            all_actions = await action_service.get_all_actions()

        # Ограничиваем до 50 результатов (лимит Telegram)
        filtered_actions = all_actions[:50]

        results = []
        sender = query.from_user

        for action_data in filtered_actions:
            action_id = action_data["id"]
            action_name = action_data["name"]
            emoji = action_data["emoji"]
            infinitive = action_data["infinitive"]

            # Формируем callback data
            # Формат: iact:{sender_id}:{action_id}:{accept=1/decline=0}
            accept_data = f"iact:{sender.id}:{action_id}:1"
            decline_data = f"iact:{sender.id}:{action_id}:0"

            # Клавиатура
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Принять", callback_data=accept_data
                        ),
                        InlineKeyboardButton(
                            text="❌ Отказаться", callback_data=decline_data
                        ),
                    ]
                ]
            )

            # Текст сообщения
            sender_link = f"[{sender.full_name}](tg://user?id={sender.id})"
            message_text = f"{emoji} {sender_link} хочет {infinitive} вами"

            # Краткое название для списка
            display_name = get_short_name(action_name)

            # Добавляем результат
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=f"{emoji} {display_name}",
                    description="",
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode="Markdown",
                    ),
                    reply_markup=keyboard,
                )
            )

        # Отправляем результаты
        await query.answer(results, cache_time=1, is_personal=True)

        logger.debug(
            f"👤 {sender.full_name} ({sender.id}) | "
            f"Запрос: '{query_text}' | "
            f"Результатов: {len(results)}"
        )

    except Exception as e:
        logger.error(f"❌ Error inline: {e}", exc_info=True)
        # Отправляем пустой результат при ошибке
        await query.answer([], cache_time=1)
