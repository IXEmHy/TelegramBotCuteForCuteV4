"""
Middleware для внедрения DB сессии и репозиториев
"""

import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.database.connection import get_session_maker
from bot.database.repositories import (
    UserRepository,
    InteractionRepository,
    ActionRepository,
    ActionStatRepository,
    AdminRepository,
)

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для предоставления DB сессии и репозиториев в handlers.
    Автоматически управляет транзакциями (commit/rollback).
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем фабрику сессий
        session_maker = get_session_maker()

        # Создаём сессию
        async with session_maker() as session:
            # Внедряем сессию и все репозитории в data
            data["db_session"] = session
            data["user_repo"] = UserRepository(session)
            data["interaction_repo"] = InteractionRepository(session)
            data["action_repo"] = ActionRepository(session)
            data["action_stat_repo"] = ActionStatRepository(session)
            data["admin_repo"] = AdminRepository(session)

            try:
                # Вызываем handler
                result = await handler(event, data)
                # Если всё ок — коммитим
                await session.commit()
                return result
            except Exception as e:
                # Если ошибка — откатываем
                await session.rollback()
                logger.error(f"Database error in handler: {e}", exc_info=True)
                raise
            finally:
                # Закрываем сессию
                await session.close()
