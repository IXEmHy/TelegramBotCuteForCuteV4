"""
Health Check Endpoints для мониторинга состояния бота

Endpoints:
- /health - базовая проверка (бот жив)
- /ready - проверка готовности (БД + Redis доступны)
- /metrics - базовые метрики (для Prometheus в будущем)
"""

import logging
from datetime import datetime
from typing import Dict, Any

from aiohttp import web

from bot.database.connection import check_database_health, check_redis_health

logger = logging.getLogger(__name__)

# Время запуска бота
_startup_time: datetime = datetime.now()


async def health_check(request: web.Request) -> web.Response:
    """
    Базовая проверка жизни бота

    Возвращает 200 OK если бот запущен.
    Используется для базовых health checks.

    GET /health
    """
    uptime = datetime.now() - _startup_time
    uptime_seconds = int(uptime.total_seconds())

    response_data = {
        "status": "healthy",
        "service": "TelegramBotCuteForCute",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime_seconds,
        "version": "4.0.0",
    }

    return web.json_response(response_data, status=200)


async def readiness_check(request: web.Request) -> web.Response:
    """
    Проверка готовности бота к работе

    Проверяет:
    - Доступность базы данных
    - Доступность Redis

    Возвращает:
    - 200 OK если все системы доступны
    - 503 Service Unavailable если есть проблемы

    GET /ready
    """
    checks: Dict[str, Any] = {
        "database": {"status": "unknown", "message": ""},
        "redis": {"status": "unknown", "message": ""},
    }

    all_healthy = True

    # Проверка базы данных
    try:
        db_ok = await check_database_health()
        checks["database"]["status"] = "healthy" if db_ok else "unhealthy"

        if not db_ok:
            checks["database"]["message"] = "Database connection failed"
            all_healthy = False

    except Exception as e:
        logger.error(f"❌ Database health check error: {e}")
        checks["database"]["status"] = "unhealthy"
        checks["database"]["message"] = str(e)
        all_healthy = False

    # Проверка Redis
    try:
        redis_ok = await check_redis_health()
        checks["redis"]["status"] = "healthy" if redis_ok else "unhealthy"

        if not redis_ok:
            checks["redis"]["message"] = "Redis connection failed"
            all_healthy = False

    except Exception as e:
        logger.error(f"❌ Redis health check error: {e}")
        checks["redis"]["status"] = "unhealthy"
        checks["redis"]["message"] = str(e)
        all_healthy = False

    # Формируем ответ
    status_code = 200 if all_healthy else 503

    response_data = {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
    }

    return web.json_response(response_data, status=status_code)


async def metrics_endpoint(request: web.Request) -> web.Response:
    """
    Базовые метрики для мониторинга

    В будущем здесь будут Prometheus метрики.
    Пока возвращаем базовую информацию.

    GET /metrics
    """
    uptime = datetime.now() - _startup_time
    uptime_seconds = int(uptime.total_seconds())

    # Базовые метрики (в будущем добавим счетчики сообщений и т.д.)
    metrics_data = {
        "bot_uptime_seconds": uptime_seconds,
        "bot_startup_timestamp": _startup_time.isoformat(),
        "bot_version": "4.0.0",
    }

    return web.json_response(metrics_data, status=200)


def setup_routes(app: web.Application) -> None:
    """Регистрация всех health check маршрутов"""
    app.router.add_get("/health", health_check)
    app.router.add_get("/ready", readiness_check)
    app.router.add_get("/metrics", metrics_endpoint)

    logger.info("✅ Health check endpoints зарегистрированы")


# Роутер для удобной интеграции
router = web.Application()
setup_routes(router)
