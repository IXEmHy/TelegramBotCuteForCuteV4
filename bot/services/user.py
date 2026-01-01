"""
Сервис для работы с пользователями
"""

import logging
from typing import Optional
from aiogram.types import User as TelegramUser

from bot.database.repositories import UserRepository
from bot.database.models import User

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для бизнес-логики работы с пользователями"""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_or_update_user(self, telegram_user: TelegramUser) -> User:
        """
        Регистрация или обновление пользователя из Telegram

        Args:
            telegram_user: Объект пользователя из aiogram

        Returns:
            User: Объект пользователя из базы данных
        """
        # Формируем full_name из first_name и last_name
        full_name_parts = [telegram_user.first_name]
        if telegram_user.last_name:
            full_name_parts.append(telegram_user.last_name)
        full_name = " ".join(full_name_parts)

        # Создаём или обновляем пользователя
        user = await self.user_repo.create_or_update(
            user_id=telegram_user.id,
            username=telegram_user.username,
            full_name=full_name,
        )

        logger.debug(f"User {user.id} (@{user.username}) registered/updated")
        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return await self.user_repo.get_by_id(user_id)

    async def get_user_display_name(self, user: User) -> str:
        """
        Получить отображаемое имя пользователя
        Приоритет: full_name -> username -> "User {id}"
        """
        if user.full_name:
            return user.full_name
        elif user.username:
            return f"@{user.username}"
        else:
            return f"User {user.id}"
