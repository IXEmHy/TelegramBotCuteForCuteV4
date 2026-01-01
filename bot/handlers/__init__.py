"""
Инициализация обработчиков
"""

from . import commands
from . import callbacks
from . import inline
from . import admin  # <--- ДОБАВЬ ЭТУ СТРОКУ

__all__ = ["commands", "callbacks", "inline", "admin"]
