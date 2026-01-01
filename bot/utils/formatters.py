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
    """
    full_name = user.full_name
    return f'<a href="tg://user?id={user.id}">{full_name}</a>'


def get_user_mention_by_id(user_id: int, name: str) -> str:
    """
    Создает кликабельное упоминание по ID и имени

    Args:
        user_id: Telegram ID пользователя
        name: Отображаемое имя

    Returns:
        str: HTML ссылка на профиль пользователя
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
        stats: Словарь со статистикой (total_sent, total_received, total_accepted, top_actions)

    Returns:
        str: Отформатированное сообщение
    """
    total_sent = stats.get("total_sent", 0)
    total_received = stats.get("total_received", 0)
    total_accepted = stats.get("total_accepted", 0)
    top_actions = stats.get("top_actions", [])

    # Вычисляем процент харизмы
    charisma = _calculate_acceptance_rate(stats)

    message = f"""<b>📊 Статистика {username}:</b>

💌 Отправлено действий: <b>{total_sent}</b>
📬 Получено действий: <b>{total_received}</b>
💖 Принято другими: <b>{total_accepted}</b>
✨ Харизма: <b>{charisma}%</b>
"""

    # Добавляем топ действий если есть
    if top_actions:
        message += "\n<b>🏆 Любимые действия:</b>\n"
        for i, (action_name, count) in enumerate(top_actions, 1):
            # Получаем эмодзи действия
            from bot.core.config import settings

            emoji = settings.action_emojis.get(action_name, "❓")

            # Склоняем слово "раз"
            if count == 1:
                times_word = "раз"
            elif 2 <= count <= 4:
                times_word = "раза"
            else:
                times_word = "раз"

            message += f"{i}. {emoji} {action_name} — {count} {times_word}\n"

    return message.strip()


def _calculate_acceptance_rate(stats: dict) -> float:
    """
    Вычисляет процент принятых взаимодействий (харизма)

    Args:
        stats: Словарь со статистикой

    Returns:
        float: Процент принятия (0.0-100.0)
    """
    total_sent = stats.get("total_sent", 0)
    if total_sent == 0:
        return 0.0

    total_accepted = stats.get("total_accepted", 0)
    return round((total_accepted / total_sent) * 100, 1)


def escape_html(text: str) -> str:
    """
    Экранирует HTML специальные символы

    Args:
        text: Исходный текст

    Returns:
        str: Текст с экранированными символами
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
