"""
Middleware для rate limiting (In-Memory)
"""

import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery


class ThrottlingMiddleware(BaseMiddleware):
    """Простой Rate limiter в памяти"""

    def __init__(self, limit: float = 0.5):
        self.limit = limit
        self.users: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id

        if user_id:
            current_time = time.time()
            last_time = self.users.get(user_id, 0)

            if current_time - last_time < self.limit:
                # Слишком часто
                return

            self.users[user_id] = current_time

        return await handler(event, data)
