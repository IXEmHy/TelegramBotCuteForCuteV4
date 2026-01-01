"""
Валидаторы для проверки данных

Используется для:
- Проверки корректности действий
- Валидации пользовательского ввода
- Защиты от некорректных данных
"""

from bot.core.config import settings


def is_valid_action(action: str) -> bool:
    """
    Проверяет, является ли действие валидным

    Args:
        action: Название действия

    Returns:
        bool: True если действие валидно, иначе False

    Example:
        >>> is_valid_action("погладить")
        True
        >>> is_valid_action("invalid_action")
        False
    """
    return action.lower() in [a.lower() for a in settings.actions]


def validate_user_id(user_id: int) -> bool:
    """
    Проверяет корректность Telegram user ID

    Args:
        user_id: ID пользователя

    Returns:
        bool: True если ID валиден

    Example:
        >>> validate_user_id(123456789)
        True
        >>> validate_user_id(-1)
        False
    """
    return isinstance(user_id, int) and user_id > 0


def can_interact_with_user(sender_id: int, receiver_id: int) -> tuple[bool, str]:
    """
    Проверяет, может ли отправитель взаимодействовать с получателем

    Args:
        sender_id: ID отправителя
        receiver_id: ID получателя

    Returns:
        tuple[bool, str]: (успех, сообщение об ошибке)

    Example:
        >>> can_interact_with_user(123, 456)
        (True, "")
        >>> can_interact_with_user(123, 123)
        (False, "Нельзя отправить действие самому себе")
    """
    if sender_id == receiver_id:
        return False, "❌ Нельзя отправить действие самому себе!"

    if not validate_user_id(sender_id) or not validate_user_id(receiver_id):
        return False, "❌ Некорректный ID пользователя"

    return True, ""
