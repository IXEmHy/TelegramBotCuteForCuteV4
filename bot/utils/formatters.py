"""
Утилиты для форматирования текста и сообщений

Используется для:
- Создания кликабельных упоминаний пользователей
- Форматирования текста действий
- Генерации красивых сообщений
"""

from aiogram.types import User


def get_user_mention(user: User) -> str:
    """
    Создает кликабельное HTML упоминание пользователя с полным именем

    Args:
        user: Объект пользователя из Telegram

    Returns:
        str: HTML ссылка вида <a href="tg://user?id=123">Имя Фамилия</a>

    Example:
        >>> user = User(id=123, first_name="Иван", last_name="Петров")
        >>> get_user_mention(user)
        '<a href="tg://user?id=123">Иван Петров</a>'
    """
    full_name = user.full_name  # Уже содержит first_name + last_name
    return f'<a href="tg://user?id={user.id}">{full_name}</a>'


def get_user_mention_by_id(user_id: int, name: str) -> str:
    """
    Создает кликабельное упоминание по ID и имени

    Args:
        user_id: Telegram ID пользователя
        name: Отображаемое имя

    Returns:
        str: HTML ссылка на профиль пользователя

    Example:
        >>> get_user_mention_by_id(123, "Иван")
        '<a href="tg://user?id=123">Иван</a>'
    """
    return f'<a href="tg://user?id={user_id}">{name}</a>'


def format_action_text(action: str, form: str = "infinitive") -> str:
    """
    Форматирует текст действия в нужную форму

    Args:
        action: Название действия (погладить, обнять и т.д.)
        form: Форма глагола ('infinitive', 'past', 'present')

    Returns:
        str: Отформатированное действие

    Example:
        >>> format_action_text("погладить", "infinitive")
        'погладить'
    """
    # Словарь форм действий (можно расширить)
    action_forms = {
        "погладить": {
            "infinitive": "погладить",
            "past": "погладил(а)",
            "present": "гладит",
        },
        "обнять": {"infinitive": "обнять", "past": "обнял(а)", "present": "обнимает"},
        "поцеловать": {
            "infinitive": "поцеловать",
            "past": "поцеловал(а)",
            "present": "целует",
        },
        "ударить": {"infinitive": "ударить", "past": "ударил(а)", "present": "бьёт"},
        "похвалить": {
            "infinitive": "похвалить",
            "past": "похвалил(а)",
            "present": "хвалит",
        },
        "подмигнуть": {
            "infinitive": "подмигнуть",
            "past": "подмигнул(а)",
            "present": "подмигивает",
        },
        "улыбнуться": {
            "infinitive": "улыбнуться",
            "past": "улыбнулся/улыбнулась",
            "present": "улыбается",
        },
        "пнуть": {"infinitive": "пнуть", "past": "пнул(а)", "present": "пинает"},
    }

    action_lower = action.lower()
    if action_lower in action_forms:
        return action_forms[action_lower].get(form, action)
    return action


def format_stats_message(username: str, stats: dict) -> str:
    """
    Форматирует сообщение со статистикой пользователя

    Args:
        username: Имя пользователя
        stats: Словарь со статистикой (sent, received, accepted)

    Returns:
        str: Отформатированное сообщение

    Example:
        >>> stats = {'sent': 10, 'received': 15, 'accepted': 12}
        >>> print(format_stats_message("Иван", stats))
    """
    message = f"""
📊 <b>Статистика пользователя {username}</b>

📤 Отправлено действий: <b>{stats["sent"]}</b>
📥 Получено действий: <b>{stats["received"]}</b>
✅ Принято действий: <b>{stats["accepted"]}</b>

💝 Процент принятия: <b>{_calculate_acceptance_rate(stats)}%</b>
"""
    return message.strip()


def _calculate_acceptance_rate(stats: dict) -> int:
    """
    Вычисляет процент принятых взаимодействий

    Args:
        stats: Словарь со статистикой

    Returns:
        int: Процент принятия (0-100)
    """
    received = stats.get("received", 0)
    if received == 0:
        return 0
    accepted = stats.get("accepted", 0)
    return int((accepted / received) * 100)


def escape_html(text: str) -> str:
    """
    Экранирует HTML специальные символы

    Args:
        text: Исходный текст

    Returns:
        str: Текст с экранированными символами

    Example:
        >>> escape_html("<script>alert('test')</script>")
        '&lt;script&gt;alert(&#x27;test&#x27;)&lt;/script&gt;'
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
