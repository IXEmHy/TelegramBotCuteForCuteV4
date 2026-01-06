"""
Точка входа в приложение Telegram бота
"""

import asyncio
import logging
import signal
from datetime import datetime

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
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
from bot.handlers import commands, callbacks, inline, admin, gender

# Health Check API
from bot.api.health import setup_routes

# Инициализация логирования
setup_logging()
logger = logging.getLogger(__name__)

# Глобальные переменные для graceful shutdown
shutdown_event = asyncio.Event()


async def set_bot_commands(bot: Bot):
    """Установка списка команд бота для разных пользователей"""

    # === КОМАНДЫ ДЛЯ ОБЫЧНЫХ ПОЛЬЗОВАТЕЛЕЙ ===
    user_commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="help", description="📖 Список действий"),
        BotCommand(command="pack", description="📦 Паки действий"),
        BotCommand(command="stats", description="📊 Моя статистика"),
        BotCommand(command="gender", description="⚧️ Настройки пола"),
    ]

    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    logger.info("✅ Команды для обычных пользователей установлены")

    # === КОМАНДЫ ДЛЯ АДМИНА ===
    admin_commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="help", description="📖 Список действий"),
        BotCommand(command="pack", description="📦 Паки действий"),
        BotCommand(command="stats", description="📊 Моя статистика"),
        BotCommand(command="gender", description="⚧️ Настройки пола"),
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
✅ Redis FSM Storage активен
✅ Health Check API: http://localhost:8080/health
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
💾 Redis соединения закрыты

⏰ Время остановки: {stop_time}
👋 До новых встреч!
"""
    await send_admin_notification(bot, shutdown_message)


def handle_signal(signum, frame):
    """Обработчик сигналов остановки (SIGINT, SIGTERM)"""
    logger.info(f"📡 Получен сигнал {signum}, инициируем graceful shutdown...")
    shutdown_event.set()


async def start_health_check_server() -> web.AppRunner:
    """
    Запуск HTTP сервера для health checks

    Returns:
        web.AppRunner: Runner для корректного завершения
    """
    app = web.Application()
    setup_routes(app)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
    await site.start()

    logger.info("✅ Health Check API запущен на http://0.0.0.0:8080")
    logger.info("   - GET /health  - базовая проверка")
    logger.info("   - GET /ready   - проверка готовности (БД + Redis)")
    logger.info("   - GET /metrics - базовые метрики")

    return runner


async def main():
    """Запуск бота"""
    logger.info("🚀 Запуск бота CuteForCute...")

    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # 1. Инициализация зависимостей
    engine = get_engine()

    # Подключаем Redis для FSM и кэша
    redis = await get_redis()

    # 2. Запуск Health Check API сервера
    health_runner = await start_health_check_server()

    # 3. Настройка бота и диспетчера
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Используем RedisStorage для FSM (состояний)
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)

    # 4. Регистрация Middleware (порядок важен!)
    dp.update.outer_middleware(ThrottlingMiddleware())
    dp.update.outer_middleware(DatabaseMiddleware())

    # 5. Регистрация Роутеров
    dp.include_router(admin.router)
    dp.include_router(gender.router)
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(inline.router)

    # 6. Запуск polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)

        # Отправляем уведомление админу о запуске
        await on_startup(bot)

        logger.info("✅ Бот успешно запущен и готов к работе!")

        # Запускаем polling с проверкой shutdown_event
        polling_task = asyncio.create_task(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        )

        # Ждем сигнала остановки
        await shutdown_event.wait()

        # Останавливаем polling
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

    except KeyboardInterrupt:
        logger.info("⚠️ Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске", exc_info=True)
    finally:
        # 7. Корректное завершение
        logger.info("🛑 Остановка бота...")

        # Отправляем уведомление админу об остановке
        try:
            await on_shutdown(bot)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить уведомление об остановке: {e}")

        # Останавливаем Health Check сервер
        try:
            await health_runner.cleanup()
            logger.info("✅ Health Check API остановлен")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при остановке Health Check API: {e}")

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
