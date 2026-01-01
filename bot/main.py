"""
Точка входа в приложение Telegram бота
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Конфигурация и логирование
from bot.core.config import settings
from bot.core.logging import setup_logging

# База данных и Redis
from bot.database.connection import get_engine, get_redis, close_redis

# Middleware
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware

# Роутеры
from bot.handlers import commands, callbacks, inline, admin

# Инициализация логирования
setup_logging()
logger = logging.getLogger(__name__)


async def main():
    """Запуск бота"""
    logger.info("🚀 Запуск бота CuteForCute...")

    # 1. Инициализация зависимостей
    engine = get_engine()

    # Подключаем Redis (для кэша)
    redis = await get_redis()

    # 2. Настройка бота и диспетчера
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Используем MemoryStorage для FSM (состояний)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # 3. Регистрация Middleware (порядок важен!)

    # Сначала Throttling (защита от спама)
    dp.update.outer_middleware(ThrottlingMiddleware())

    # Затем Database (создает сессию и внедряет репозитории)
    dp.update.outer_middleware(DatabaseMiddleware())

    # 4. Регистрация Роутеров
    dp.include_router(admin.router)  # Админка (должна быть первой)
    dp.include_router(commands.router)  # Базовые команды (/start, /help, /stats)
    dp.include_router(callbacks.router)  # Обработка кнопок
    dp.include_router(inline.router)  # Inline режим

    # 5. Запуск polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Бот успешно запущен и готов к работе!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}", exc_info=True)
    finally:
        # 6. Корректное завершение
        logger.info("🛑 Остановка бота...")
        await close_redis()
        await engine.dispose()
        logger.info("👋 Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен вручную")
