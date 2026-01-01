"""
Сервис кэширования с использованием Redis

ВОЗМОЖНОСТИ:
- Кэширование списка активных действий
- Автоматическое обновление при изменениях
- Fallback на БД если Redis недоступен
"""

import json
import logging
from typing import Optional, Any
from redis.asyncio import Redis
from redis.exceptions import RedisError
from bot.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Сервис для работы с Redis кэшем"""

    # Ключи кэша
    ACTIONS_KEY = "bot:actions:all"
    ACTION_BY_NAME_PREFIX = "bot:action:name:"

    # Время жизни кэша (секунды)
    ACTIONS_TTL = 300  # 5 минут
    ACTION_TTL = 600  # 10 минут

    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Args:
            redis_client: Клиент Redis (опционально)
        """
        self.redis = redis_client
        self._enabled = redis_client is not None

    async def get_actions(self) -> Optional[list[dict]]:
        """
        Получить все действия из кэша

        Returns:
            list[dict] | None: Список действий или None если нет в кэше
        """
        if not self._enabled:
            return None

        try:
            data = await self.redis.get(self.ACTIONS_KEY)
            if data:
                logger.debug("✅ Действия загружены из кэша")
                return json.loads(data)
            return None
        except RedisError as e:
            logger.warning(f"⚠️ Redis error при чтении действий: {e}")
            return None

    async def set_actions(self, actions: list[dict]) -> bool:
        """
        Сохранить действия в кэш

        Args:
            actions: Список действий (словари)

        Returns:
            bool: Успешность операции
        """
        if not self._enabled:
            return False

        try:
            await self.redis.setex(
                self.ACTIONS_KEY,
                self.ACTIONS_TTL,
                json.dumps(actions, ensure_ascii=False),
            )
            logger.debug(f"✅ {len(actions)} действий сохранены в кэш")
            return True
        except RedisError as e:
            logger.warning(f"⚠️ Redis error при записи действий: {e}")
            return False

    async def get_action_by_name(self, name: str) -> Optional[dict]:
        """
        Получить одно действие по имени из кэша

        Args:
            name: Название действия

        Returns:
            dict | None: Данные действия или None
        """
        if not self._enabled:
            return None

        try:
            key = f"{self.ACTION_BY_NAME_PREFIX}{name}"
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except RedisError as e:
            logger.warning(f"⚠️ Redis error при чтении действия {name}: {e}")
            return None

    async def set_action(self, name: str, action_data: dict) -> bool:
        """
        Сохранить одно действие в кэш

        Args:
            name: Название действия
            action_data: Данные действия

        Returns:
            bool: Успешность операции
        """
        if not self._enabled:
            return False

        try:
            key = f"{self.ACTION_BY_NAME_PREFIX}{name}"
            await self.redis.setex(
                key, self.ACTION_TTL, json.dumps(action_data, ensure_ascii=False)
            )
            return True
        except RedisError as e:
            logger.warning(f"⚠️ Redis error при записи действия {name}: {e}")
            return False

    async def invalidate_actions(self) -> bool:
        """
        Инвалидировать весь кэш действий
        (вызывается при изменении действий в админке)

        Returns:
            bool: Успешность операции
        """
        if not self._enabled:
            return False

        try:
            # Удаляем общий список
            await self.redis.delete(self.ACTIONS_KEY)

            # Удаляем все индивидуальные действия
            pattern = f"{self.ACTION_BY_NAME_PREFIX}*"
            async for key in self.redis.scan_iter(match=pattern):
                await self.redis.delete(key)

            logger.info("🔄 Кэш действий инвалидирован")
            return True
        except RedisError as e:
            logger.warning(f"⚠️ Redis error при инвалидации: {e}")
            return False

    async def ping(self) -> bool:
        """
        Проверить доступность Redis

        Returns:
            bool: True если Redis доступен
        """
        if not self._enabled:
            return False

        try:
            await self.redis.ping()
            return True
        except RedisError:
            return False


# ========== ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР ==========

_cache_service: Optional[CacheService] = None


async def get_cache_service(redis: Optional[Redis] = None) -> CacheService:
    """
    Получить глобальный экземпляр CacheService

    Args:
        redis: Redis клиент (опционально, для инициализации)

    Returns:
        CacheService: Сервис кэширования
    """
    global _cache_service

    if _cache_service is None:
        _cache_service = CacheService(redis)

    return _cache_service
