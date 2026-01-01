"""
Обработчики команд бота
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.database.repositories import (
    UserRepository,
    ActionRepository,
    ActionStatRepository,
)
from bot.services.user import UserService
from bot.utils.formatters import format_stats_message
from bot.keyboards.reply_kb import get_user_main_keyboard, get_admin_main_keyboard
from bot.core.config import settings

router = Router(name="commands")
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message, user_repo: UserRepository):
    """Обработка команды /start"""
    user = message.from_user

    # Регистрация/обновление пользователя
    user_service = UserService(user_repo)
    await user_service.register_or_update_user(user)

    # Проверка на админа
    is_admin = user.id == settings.admin_id

    # Выбор клавиатуры
    keyboard = get_admin_main_keyboard() if is_admin else get_user_main_keyboard()

    role_info = "\n<b>Вы администратор.</b>" if is_admin else ""

    welcome_text = (
        f"<b>👋 Привет, {user.full_name}!</b>{role_info}\n\n"
        "🤖 Добро пожаловать в <code>CuteForCuteBot</code>!\n\n"
        "Используй инлайн-режим для отправки милых действий друзьям!\n\n"
        "<b>📖 Как использовать:</b>\n"
        "1. Перейди в любой чат\n"
        "2. Напиши <code>@CuteForCuteBot</code> и название действия\n"
        "3. Выбери действие из списка\n"
        "4. Отправь другу!\n\n"
        "<i>Получатель сможет принять или отклонить действие.</i>"
    )

    await message.answer(welcome_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "📜 Доступные действия")
@router.message(F.text == "📚 Все действия")
@router.message(Command("help"))
async def cmd_help(message: Message, action_repo: ActionRepository):
    """Показать доступные паки действий"""

    # Получаем все паки
    packs = await action_repo.get_all_packs()

    text_parts = ["<b>📦 Доступные паки действий:</b>\n"]

    for pack_name, actions in packs.items():
        # Показываем название пака и первые 3 действия
        preview_actions = actions[:3]
        action_list = ", ".join(
            [f"{action['emoji']} {action['name']}" for action in preview_actions]
        )

        total = len(actions)
        text_parts.append(
            f"\n<b>{pack_name}</b> ({total} действий):\n{action_list}...\n"
        )

    text_parts.append(
        "\n<i>💡 Чтобы увидеть все действия пака:</i>\n"
        "<code>/pack Название пака</code>\n\n"
        "<i>🎯 Используйте inline-режим для отправки:</i>\n"
        "<code>@CuteForCuteBot</code> <i>название_действия</i>"
    )

    text = "".join(text_parts)
    await message.answer(text[:4000], parse_mode="HTML")


@router.message(Command("pack"))
async def cmd_pack(message: Message, action_repo: ActionRepository):
    """Показать все действия в конкретном паке"""

    # Получаем аргументы команды
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        # Показываем список паков
        pack_names = await action_repo.get_pack_names()
        text = (
            "<b>📦 Доступные паки:</b>\n\n"
            + "\n".join([f"• {name}" for name in pack_names])
            + "\n\n<i>Используйте:</i> <code>/pack Название пака</code>"
        )
        await message.answer(text, parse_mode="HTML")
        return

    pack_name = args[1]
    pack_actions = await action_repo.get_pack_actions(pack_name)

    if not pack_actions:
        await message.answer(
            f"❌ Пак <b>'{pack_name}'</b> не найден.\n\n"
            "Используйте <code>/pack</code> для списка паков.",
            parse_mode="HTML",
        )
        return

    # Формируем список действий
    lines = [f"{action['emoji']} {action['name']}" for action in pack_actions]

    # Разбиваем на колонки по 3
    columns = []
    for i in range(0, len(lines), 3):
        chunk = lines[i : i + 3]
        columns.append(" • " + "\n • ".join(chunk))

    text = (
        f"<b>📦 Пак: {pack_name}</b>\n"
        f"<i>Всего действий: {len(pack_actions)}</i>\n\n" + "\n\n".join(columns)
    )

    await message.answer(text[:4000], parse_mode="HTML")


@router.message(F.text == "ℹ️ Как использовать")
async def use_bot_info(message: Message):
    """Инструкция по использованию бота"""
    await message.answer(
        "<b>📖 Как использовать бота:</b>\n\n"
        "1. Перейди в любой чат или группу\n"
        "2. Начни вводить <code>@CuteForCuteBot</code> и название действия\n"
        "3. Выбери нужное действие из списка\n"
        "4. Отправь!\n\n"
        "<i>Получатель сможет принять или отклонить твоё действие.</i>",
        parse_mode="HTML",
    )


@router.message(F.text == "📊 Моя статистика")
@router.message(Command("stats"))
async def cmd_stats(
    message: Message,
    user_repo: UserRepository,
    action_stat_repo: ActionStatRepository,
):
    """Показать статистику пользователя"""
    user = message.from_user

    # Сначала регистрируем/обновляем пользователя
    user_service = UserService(user_repo)
    await user_service.register_or_update_user(user)

    # Получаем пользователя из БД
    target_user = await user_service.get_user(user.id)

    if not target_user:
        await message.answer("❌ Пользователь не найден в базе данных.")
        return

    # Получаем статистику
    stats = await action_stat_repo.get_user_stats(target_user.id)

    # Форматируем и отправляем
    text = format_stats_message(user.full_name, stats)
    await message.answer(text, parse_mode="HTML")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ-панель (заглушка)"""
    if message.from_user.id != settings.admin_id:
        return

    text = (
        "<b>⚙️ Админ-панель</b>\n\n"
        "Доступные команды:\n"
        "• <code>/stats_global</code> - Глобальная статистика\n"
        "• <code>/broadcast</code> - Рассылка\n"
    )
    await message.answer(text, parse_mode="HTML")
