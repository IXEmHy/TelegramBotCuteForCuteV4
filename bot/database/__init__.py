"""
Database package initialization
"""

from bot.database.connection import DatabaseConnection, get_redis, close_redis
from bot.database.models import Base, User, Interaction, InteractionStatus
from bot.database.repositories import (
    UserRepository,
    ActionRepository,
    InteractionRepository,
    ActionStatRepository,
    AdminRepository,
)

# Convenience functions
get_engine = DatabaseConnection.get_engine
get_session_maker = DatabaseConnection.get_session_maker  # ✅ ИСПРАВЛЕНО
init_db = DatabaseConnection.init_db

__all__ = [
    # Connection
    "DatabaseConnection",
    "get_engine",
    "get_session_maker",  # ✅ ИСПРАВЛЕНО
    "get_redis",
    "close_redis",
    "init_db",
    # Models
    "Base",
    "User",
    "Interaction",
    "InteractionStatus",
    # Repositories
    "UserRepository",
    "ActionRepository",
    "InteractionRepository",
    "ActionStatRepository",
    "AdminRepository",
]
