"""
Сервис для работы с действиями

ФУНКЦИОНАЛ:
- Загрузка действий из БД с кэшированием
- Поиск действий
- Обновление статистики использования
"""

import logging
from typing import Optional
from bot.database.repositories import ActionRepository, ActionStatRepository
from bot.services.cache import CacheService
from bot.database.models import Action

logger = logging.getLogger(__name__)


class ActionService:
    """Сервис для работы с действиями"""

    def __init__(
        self,
        action_repo: ActionRepository,
        cache: Optional[CacheService] = None,
        action_stat_repo: Optional[ActionStatRepository] = None,
    ):
        self.action_repo = action_repo
        self.cache = cache
        self.action_stat_repo = action_stat_repo

    async def get_all_actions(self) -> list[dict]:
        """
        Получить все активные действия (с кэшированием)

        Returns:
            list[dict]: Список действий в формате:
                {
                    'id': int,
                    'name': str,
                    'emoji': str,
                    'infinitive': str,
                    'past_tense': str,
                    'genitive_noun': str,
                    'display_order': int,
                    'pack': str
                }
        """
        # Пытаемся получить из кэша
        if self.cache:
            cached = await self.cache.get_actions()
            if cached:
                logger.debug(f"📦 Загружено {len(cached)} действий из кэша")
                return cached

        # Загружаем из БД
        actions = await self.action_repo.get_all_active()

        # ✅ ИСПРАВЛЕНО: ActionRepository уже возвращает list[dict]
        # Сохраняем в кэш напрямую
        if self.cache:
            await self.cache.set_actions(actions)

        logger.debug(f"💾 Загружено {len(actions)} действий из БД")
        return actions

    async def get_action_by_name(self, name: str) -> Optional[dict]:
        """
        Получить действие по имени

        Args:
            name: Название действия (например, "Обнять")

        Returns:
            dict | None: Данные действия или None
        """
        # Пытаемся из кэша
        if self.cache:
            cached = await self.cache.get_action_by_name(name)
            if cached:
                return cached

        # Из БД
        action = await self.action_repo.get_by_name(name)
        if not action:
            return None

        # Сохраняем в кэш
        if self.cache:
            await self.cache.set_action(name, action)

        return action

    async def search_actions(self, query: str) -> list[dict]:
        """
        Поиск действий по части названия

        Args:
            query: Поисковый запрос

        Returns:
            list[dict]: Найденные действия
        """
        actions = await self.action_repo.search(query)
        return actions

    async def increment_usage(self, action_name: str, user_id: int):
        """
        Увеличить счётчики использования действия

        Args:
            action_name: Название действия
            user_id: ID пользователя (отправителя)
        """
        # Увеличиваем общий счётчик
        await self.action_repo.increment_usage(action_name)

        # Увеличиваем персональный счётчик
        if self.action_stat_repo:
            await self.action_stat_repo.increment_sent(user_id, action_name)

    async def invalidate_cache(self):
        """
        Инвалидировать кэш действий
        (вызывается после изменений в админке)
        """
        if self.cache:
            await self.cache.invalidate_actions()
            logger.info("🔄 Кэш действий очищен")
