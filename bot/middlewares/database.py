"""
Middleware для внедрения DB сессии
"""

import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.connection import DatabaseConnection
from bot.database.repositories import UserRepository, InteractionRepository

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """Middleware для предоставления DB сессии в handlers"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session_maker = DatabaseConnection.get_session_maker()
        async with session_maker() as session:
            # Внедряем сессию и репозитории
            data["db_session"] = session
            data["user_repo"] = UserRepository(session)
            data["interaction_repo"] = InteractionRepository(session)

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error: {e}", exc_info=True)
                raise
            finally:
                await session.close()
