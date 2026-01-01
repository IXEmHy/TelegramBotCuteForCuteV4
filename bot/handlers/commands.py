"""
Базовые команды бота (/start, /help, /stats)
"""

import logging

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.core.config import settings
from bot.database.repositories import UserRepository, ActionStatRepository
from bot.services.user import UserService
from bot.keyboards.reply_kb import get_user_main_keyboard, get_admin_main_keyboard

router = Router(name="commands")
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, user_repo: UserRepository):
    """Обработчик команды /start"""
    user_service = UserService(user_repo)
    await user_service.register_or_update_user(message.from_user)

    # Выбираем клавиатуру в зависимости от того, админ ли пользователь
    is_admin = message.from_user.id == settings.admin_id
    keyboard = get_admin_main_keyboard() if is_admin else get_user_main_keyboard()

    welcome_text = f"👋 Привет, {message.from_user.full_name}!\n\n"

    if is_admin:
        welcome_text += (
            "🔐 <b>Режим администратора активирован</b>\n\n"
            "Я бот для РП действий. Используй меня в любом чате:\n"
            "<code>@CuteForCuteBot обнять</code>\n\n"
            "📜 Список всех действий доступен в инлайн-режиме.\n"
            "⚙️ Админка: /admin"
        )
    else:
        welcome_text += (
            "Я бот для РП действий. Используй меня в любом чате:\n"
            "<code>@CuteForCuteBot обнять</code>\n\n"
            "📜 Список всех действий доступен в инлайн-режиме."
        )

    await message.answer(welcome_text, reply_markup=keyboard)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📚 <b>Помощь</b>\n\n"
        "1. Введите <code>@CuteForCuteBot</code> в любом чате\n"
        "2. Выберите действие из списка\n"
        "3. Получатель сможет принять или отклонить его\n\n"
        "📊 <b>Команды:</b>\n"
        "/stats - Ваша статистика\n"
        "/stats (в ответ) - Статистика пользователя\n"
        "/admin - Админ-панель (для владельца)"
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
        f"📊 <b>Статистика {target_user.full_name}:</b>\n\n"
        f"💌 Отправлено действий: <code>{sent}</code>\n"
        f"📬 Получено действий: <code>{received}</code>\n"
        f"💖 Принято другими: <code>{accepted}</code>\n"
        f"✨ Харизма: <code>{success_rate:.1f}%</code>\n\n"
    )

    if stats["top_actions"]:
        text += "🏆 <b>Любимые действия:</b>\n"
        for idx, (name, count) in enumerate(stats["top_actions"], 1):
            text += f"{idx}. {name.capitalize()} — {count} раз\n"

    await message.answer(text)


# ========== ОБРАБОТЧИКИ КНОПОК REPLY KEYBOARD ==========


@router.message(F.text == "✨ Использовать бота")
async def button_use_bot(message: Message):
    """Обработчик кнопки 'Использовать бота'"""
    await message.answer(
        "💡 Чтобы использовать бота:\n\n"
        "1. Откройте любой чат\n"
        "2. Напишите <code>@CuteForCuteBot</code>\n"
        "3. Выберите действие из списка\n\n"
        "Попробуйте прямо сейчас! 👇"
    )


@router.message(F.text == "📜 Список действий")
async def button_action_list(message: Message):
    """Обработчик кнопки 'Список действий'"""
    await message.answer(
        "📜 <b>Доступные действия:</b>\n\n"
        "Чтобы увидеть полный список действий, начните вводить:\n"
        "<code>@CuteForCuteBot</code>\n\n"
        "Бот покажет все доступные действия в инлайн-режиме!"
    )


@router.message(F.text == "📊 Моя статистика")
async def button_my_stats(
    message: Message, user_repo: UserRepository, action_stat_repo: ActionStatRepository
):
    """Обработчик кнопки 'Моя статистика'"""
    await cmd_stats(message, user_repo, action_stat_repo)


@router.message(F.text == "📖 Помощь")
async def button_help(message: Message):
    """Обработчик кнопки 'Помощь'"""
    await cmd_help(message)
