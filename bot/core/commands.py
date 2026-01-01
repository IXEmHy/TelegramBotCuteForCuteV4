"""
Централизованные команды и тексты кнопок
Все тексты кнопок и команд определены здесь
"""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class BotCommands:
    """Все команды и тексты кнопок бота"""

    # === ОСНОВНЫЕ КОМАНДЫ ===
    START: Final[str] = "/start"
    HELP: Final[str] = "/help"
    STATS: Final[str] = "/stats"
    PACK: Final[str] = "/pack"
    ADMIN: Final[str] = "/admin"

    # === КНОПКИ ГЛАВНОГО МЕНЮ ===
    BTN_ACTIONS: Final[str] = "📜 Доступные действия"
    BTN_HOW_TO_USE: Final[str] = "ℹ️ Как использовать"
    BTN_MY_STATS: Final[str] = "📊 Моя статистика"

    # === КНОПКИ АДМИН-ПАНЕЛИ ===
    BTN_ADMIN_STATS: Final[str] = "👥 Статистика"
    BTN_ADMIN_ACTIONS: Final[str] = "🔧 Управление действиями"
    BTN_ADMIN_TEST: Final[str] = "🧪 Тест команд"
    BTN_ADMIN_EXIT: Final[str] = "⬅️ Выйти"

    # === ОПИСАНИЯ ДЛЯ МЕНЮ TELEGRAM ===
    DESC_START: Final[str] = "🚀 Запустить бота"
    DESC_HELP: Final[str] = "📦 Доступные паки"
    DESC_PACK: Final[str] = "📚 Действия в паке"
    DESC_STATS: Final[str] = "📊 Моя статистика"
    DESC_ADMIN: Final[str] = "⚙️ Админ-панель"


# Глобальный экземпляр
CMD = BotCommands()
