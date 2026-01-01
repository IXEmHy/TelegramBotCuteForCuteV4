"""
Middleware для внедрения репозиториев в обработчики
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import (
    UserRepository,
    InteractionRepository,
    ActionRepository,
    ActionStatRepository,
    AdminRepository,
)


class RepositoryMiddleware(BaseMiddleware):
    """
    Middleware, который инициализирует репозитории и передает их в handler.
    Требует наличия 'session' в data (должен идти ПОСЛЕ DatabaseMiddleware).
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession = data.get("session")

        if session:
            # Инициализация репозиториев
            data["user_repo"] = UserRepository(session)
            data["interaction_repo"] = InteractionRepository(session)
            data["action_repo"] = ActionRepository(session)
            data["action_stat_repo"] = ActionStatRepository(session)
            data["admin_repo"] = AdminRepository(session)

        return await handler(event, data)
