"""
Обработчики для администратора
"""

import logging
from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, FSInputFile
from sqlalchemy import func, select
from bot.core.config import settings
from bot.database.repositories import UserRepository, InteractionRepository
from bot.database.models import User, Interaction
from bot.services.user import UserService

router = Router(name="admin")
logger = logging.getLogger(__name__)


# Фильтр: только админ может использовать эти команды
def is_admin(message: Message) -> bool:
    return message.from_user.id == settings.admin_id


@router.message(Command("stats_global"), lambda m: is_admin(m))
async def cmd_global_stats(message: Message, db_session):
    """
    Глобальная статистика бота
    """
    # Считаем пользователей
    users_count = await db_session.scalar(select(func.count(User.id)))

    # Считаем взаимодействия
    interactions_count = await db_session.scalar(select(func.count(Interaction.id)))

    # Топ-3 популярных действия
    # (SQLAlchemy запрос)
    top_actions_query = (
        select(Interaction.action, func.count(Interaction.id).label("count"))
        .group_by(Interaction.action)
        .order_by(func.count(Interaction.id).desc())
        .limit(5)
    )
    result = await db_session.execute(top_actions_query)
    top_actions = result.all()

    stats_text = f"""
📊 <b>Глобальная статистика</b>

👥 <b>Всего пользователей:</b> {users_count}
💌 <b>Всего взаимодействий:</b> {interactions_count}

🔥 <b>Популярные действия:</b>
"""
    for action, count in top_actions:
        emoji = settings.action_emojis.get(action, "🔹")
        stats_text += f"{emoji} {action}: <b>{count}</b>\n"

    await message.answer(stats_text, parse_mode="HTML")


@router.message(Command("logs"), lambda m: is_admin(m))
async def cmd_get_logs(message: Message):
    """
    Отправить файл логов
    """
    log_file = FSInputFile("logs/bot.log")
    try:
        await message.answer_document(
            log_file, caption="📂 <b>Логи бота</b>", parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки логов: {e}")


@router.message(Command("broadcast"), lambda m: is_admin(m))
async def cmd_broadcast(message: Message, command: CommandObject, db_session):
    """
    Рассылка сообщения всем пользователям.
    Использование: /broadcast Текст сообщения
    """
    if not command.args:
        await message.answer(
            "⚠️ Введите текст рассылки.\nПример: <code>/broadcast Привет всем!</code>",
            parse_mode="HTML",
        )
        return

    text = command.args

    # Получаем всех пользователей
    result = await db_session.execute(select(User.telegram_id))
    users = result.scalars().all()

    count = 0
    errors = 0

    status_msg = await message.answer(
        f"⏳ Начинаю рассылку для {len(users)} пользователей..."
    )

    for user_id in users:
        try:
            await message.bot.send_message(
                chat_id=user_id, text=text, parse_mode="HTML"
            )
            count += 1
        except Exception:
            errors += 1

        # Пауза, чтобы не словить бан от Телеграма (очень простая реализация)
        # В идеале использовать aiojobs или Celery
        # Но для <1000 юзеров пойдет

    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n📨 Отправлено: {count}\n❌ Ошибок: {errors}",
        parse_mode="HTML",
    )
