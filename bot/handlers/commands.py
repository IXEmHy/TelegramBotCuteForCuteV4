"""
Базовые команды бота (/start, /help, /stats)
"""

import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.database.repositories import UserRepository, ActionStatRepository
from bot.services.user import UserService

router = Router(name="commands")
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, user_repo: UserRepository):
    """Обработчик команды /start"""
    user_service = UserService(user_repo)
    await user_service.register_or_update_user(message.from_user)

    await message.answer(
        f"👋 Привет, {message.from_user.full_name}!\n\n"
        "Я бот для РП действий. Используй меня в любом чате:\n"
        "`@bot <действие>`\n\n"
        "Например: `@CuteForCuteBot обнять`\n\n"
        "📜 Список всех действий доступен в инлайн-режиме.",
        parse_mode="Markdown",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📚 **Помощь**\n\n"
        "1. Введите `@bot_name` в любом чате\n"
        "2. Выберите действие из списка\n"
        "3. Получатель сможет принять или отклонить его\n\n"
        "📊 **Команды:**\n"
        "/stats - Ваша статистика\n"
        "/stats (в ответ) - Статистика пользователя\n"
        "/admin - Админ-панель (для владельца)",
        parse_mode="Markdown",
    )


@router.message(Command("stats", "me"))
async def cmd_stats(
    message: Message, user_repo: UserRepository, action_stat_repo: ActionStatRepository
):
    """Личная статистика или статистика пользователя из реплая"""
    target_user = message.from_user
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user

    user_service = UserService(user_repo)
    await user_service.register_or_update_user(target_user)

    stats = await action_stat_repo.get_user_stats(target_user.id)

    sent = stats["total_sent"]
    received = stats["total_received"]
    accepted = stats["total_accepted"]

    success_rate = 0
    if received > 0:
        success_rate = (accepted / received) * 100

    text = (
        f"📊 **Статистика {target_user.full_name}:**\n\n"
        f"💌 Отправлено действий: `{sent}`\n"
        f"📬 Получено действий: `{received}`\n"
        f"💖 Принято другими: `{accepted}`\n"
        f"✨ Харизма: `{success_rate:.1f}%`\n\n"
    )

    if stats["top_actions"]:
        text += "🏆 **Любимые действия:**\n"
        for idx, (name, count) in enumerate(stats["top_actions"], 1):
            text += f"{idx}. {name.capitalize()} — {count} раз\n"

    await message.answer(text, parse_mode="Markdown")
