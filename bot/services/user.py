"""
Сервис для работы с пользователями

Содержит бизнес-логику:
- Регистрация/обновление пользователей
- Получение статистики
- Проверка существования
"""

from typing import Optional
from aiogram.types import User as TelegramUser

from bot.database.repositories import UserRepository
from bot.database.models import User


class UserService:
    """Сервис для работы с пользователями"""

    def __init__(self, user_repo: UserRepository):
        """
        Инициализация сервиса

        Args:
            user_repo: Репозиторий пользователей
        """
        self.user_repo = user_repo

    async def register_or_update_user(self, telegram_user: TelegramUser) -> User:
        """
        Регистрирует нового пользователя или обновляет существующего

        Args:
            telegram_user: Объект пользователя из Telegram

        Returns:
            User: Модель пользователя из БД
        """
        return await self.user_repo.create_or_update(
            user_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
        )

    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Получает пользователя по ID

        Args:
            user_id: Telegram ID пользователя

        Returns:
            Optional[User]: Пользователь или None
        """
        return await self.user_repo.get_by_id(user_id)

    async def get_user_stats(self, user_id: int) -> dict:
        """
        Получает статистику пользователя

        Args:
            user_id: Telegram ID пользователя

        Returns:
            dict: Словарь со статистикой {sent, received, accepted}
        """
        return await self.user_repo.get_stats(user_id)

    async def user_exists(self, user_id: int) -> bool:
        """
        Проверяет существование пользователя

        Args:
            user_id: Telegram ID

        Returns:
            bool: True если пользователь существует
        """
        user = await self.get_user(user_id)
        return user is not None
