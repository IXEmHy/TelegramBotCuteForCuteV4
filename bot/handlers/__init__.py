"""
Инициализация обработчиков
"""

from . import commands
from . import callbacks
from . import inline
from . import admin
from . import gender  # ← ДОБАВЛЕНА СТРОКА

__all__ = ["commands", "callbacks", "inline", "admin", "gender"]  # ← ДОБАВЛЕН "gender"
