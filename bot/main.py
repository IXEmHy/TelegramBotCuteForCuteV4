"""
Точка входа в приложение Telegram бота
"""

import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

# Конфигурация и логирование
from bot.core.config import settings
from bot.core.logging import setup_logging

# База данных и Redis
from bot.database.connection import get_engine, get_redis, close_redis

# Middleware
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware

# Роутеры
from bot.handlers import commands, callbacks, inline, admin, gender  # ← ДОБАВЛЕН gender

# Инициализация логирования
setup_logging()
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    """Установка списка команд бота для разных пользователей"""

    # === КОМАНДЫ ДЛЯ ОБЫЧНЫХ ПОЛЬЗОВАТЕЛЕЙ ===
    user_commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="help", description="📖 Список действий"),
        BotCommand(command="pack", description="📦 Паки действий"),
        BotCommand(command="stats", description="📊 Моя статистика"),
        BotCommand(command="gender", description="⚧️ Настройки пола"),  # ← ДОБАВЛЕНО
    ]

    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    logger.info("✅ Команды для обычных пользователей установлены")

    # === КОМАНДЫ ДЛЯ АДМИНА ===
    admin_commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="help", description="📖 Список действий"),
        BotCommand(command="pack", description="📦 Паки действий"),
        BotCommand(command="stats", description="📊 Моя статистика"),
        BotCommand(command="gender", description="⚧️ Настройки пола"),  # ← ДОБАВЛЕНО
        BotCommand(command="stats_global", description="📊 Глобальная статистика"),
        BotCommand(command="add_action", description="➕ Добавить действие"),
        BotCommand(command="list_actions", description="📋 Список действий"),
        BotCommand(command="cache_clear", description="🗑 Очистить кэш"),
        BotCommand(command="broadcast", description="📢 Рассылка"),
    ]

    await bot.set_my_commands(
        admin_commands, scope=BotCommandScopeChat(chat_id=settings.admin_id)
    )
    logger.info("✅ Команды для администратора установлены")


async def send_admin_notification(bot: Bot, message: str):
    """Отправка уведомления администратору"""
    try:
        await bot.send_message(
            chat_id=settings.admin_id, text=message, parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"⚠️ Не удалось отправить уведомление админу: {e}")


async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    try:
        logger.info("⏳ Запуск систем бота...")

        # Устанавливаем команды бота
        await set_bot_commands(bot)

        # Форматирование времени
        start_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        startup_message = f"""
🚀 <b>БОТ ЗАПУЩЕН</b>

✅ Все системы активны
✅ База данных подключена
✅ Обработчики загружены
✅ Система выбора пола активна

⏰ Время запуска: {start_time}
🤖 Бот готов к работе!
"""
        await send_admin_notification(bot, startup_message)

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске: {e}")


async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    logger.info("⚠️ Получен сигнал остановки...")

    stop_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    shutdown_message = f"""
🛑 <b>БОТ ОСТАНОВЛЕН</b>

⚠️ Все системы отключены
💾 Соединения с БД закрыты

⏰ Время остановки: {stop_time}
👋 До новых встреч!
"""
    await send_admin_notification(bot, shutdown_message)


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
    dp.include_router(gender.router)  # ← ДОБАВЛЕН: Выбор/изменение пола
    dp.include_router(commands.router)  # Базовые команды (/start, /help, /stats)
    dp.include_router(callbacks.router)  # Обработка кнопок
    dp.include_router(inline.router)  # Inline режим

    # 5. Запуск polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)

        # Отправляем уведомление админу о запуске
        await on_startup(bot)

        logger.info("✅ Бот успешно запущен и готов к работе!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except KeyboardInterrupt:
        logger.info("⚠️ Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске", exc_info=True)
    finally:
        # 6. Корректное завершение
        logger.info("🛑 Остановка бота...")

        # Отправляем уведомление админу об остановке (с обработкой ошибок)
        try:
            await on_shutdown(bot)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить уведомление об остановке: {e}")

        # Закрываем соединения
        try:
            await close_redis()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при закрытии Redis: {e}")

        try:
            await engine.dispose()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при закрытии БД: {e}")

        # Закрываем сессию бота
        try:
            await bot.session.close()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при закрытии сессии бота: {e}")

        logger.info("👋 Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Бот остановлен вручную")
