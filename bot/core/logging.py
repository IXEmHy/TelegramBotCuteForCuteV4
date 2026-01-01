"""
Настройка системы логирования
"""

import logging
import sys
import codecs
from pathlib import Path


def setup_logging() -> logging.Logger:
    """Настраивает систему логирования"""
    # 1. Исправляем кодировку консоли Windows
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

    # Создаем папку для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "bot.log"

    # Форматы
    file_format = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
    console_format = "%(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    # === HANDLER 1: ФАЙЛ (Все логи, включая ошибки) ===
    file_handler = logging.FileHandler(
        filename=log_file,
        mode="w",  # Перезаписываем файл при каждом запуске
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(file_format, date_format))
    root_logger.addHandler(file_handler)

    # === HANDLER 2: КОНСОЛЬ (Только статус + краткие ошибки) ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(console_format))

    # Фильтр: в консоль только статусные сообщения и краткие ошибки
    class ConsoleFilter(logging.Filter):
        # Только эти иконки попадают в консоль
        ALLOWED_ICONS = ["🚀", "✅", "⏳", "🛑", "👋", "⚠️", "❌"]

        def filter(self, record):
            msg = record.getMessage()

            # Пускаем статусные сообщения
            if any(icon in msg for icon in self.ALLOWED_ICONS):
                return True

            # Для ошибок (ERROR уровень) - только краткое сообщение
            if record.levelno >= logging.ERROR:
                # Убираем трейсбек из консоли, оставляем только текст ошибки
                record.msg = f"❌ Ошибка: {record.getMessage().split(chr(10))[0]}"
                record.msg += "\n   📄 Подробности в файле: logs/bot.log"
                record.exc_info = None  # Убираем трейсбек
                return True

            return False

    console_handler.addFilter(ConsoleFilter())
    root_logger.addHandler(console_handler)

    # Заглушаем лишние логи от библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    return logging.getLogger(__name__)
