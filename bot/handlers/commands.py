"""
Обработчики команд бота
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from bot.database.repositories import UserRepository
from bot.services.user import UserService
from bot.utils.formatters import format_stats_message
from bot.keyboards.reply_kb import get_user_main_keyboard, get_admin_main_keyboard
from bot.core.config import settings

router = Router(name="commands")
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message, user_repo: UserRepository):
    """Команда /start"""
    user_service = UserService(user_repo)
    await user_service.register_or_update_user(message.from_user)

    is_admin = message.from_user.id == settings.admin_id
    keyboard = get_admin_main_keyboard() if is_admin else get_user_main_keyboard()

    role_info = "\n👨‍💻 <b>Вы авторизованы как Администратор.</b>" if is_admin else ""

    welcome_text = f"""
👋 <b>Добро пожаловать в CuteBot!</b>
{role_info}

✨ Чтобы использовать бота в других чатах:
Просто напишите <code>@CuteForCutebot</code> в поле ввода и выберите действие!

👇 <b>Используйте меню для навигации:</b>
"""
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ-меню (только через команду)"""
    if message.from_user.id != settings.admin_id:
        return  # Игнорируем обычных пользователей

    text = """
🛠 <b>Панель администратора</b>

Доступные команды:
• /stats_global — Общая статистика
• /broadcast — Рассылка (в разработке)
"""
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "✨ Использовать бота")
async def use_bot_info(message: Message):
    """Инструкция без лишних кнопок"""
    await message.answer(
        "📝 <b>Как использовать:</b>\n\n"
        "1. Откройте любой чат с другом\n"
        "2. Напишите: <code>@CuteForCutebot</code>\n"
        "3. Подождите пару секунд, появится список\n"
        "4. Выберите действие!\n\n"
        "💡 <i>Если список не появляется, убедитесь, что вы не допустили ошибку в имени бота.</i>",
        parse_mode="HTML",
    )


@router.message(F.text == "📜 Список действий")
async def actions_list_button(message: Message):
    """Показать список действий текстом"""
    actions = settings.actions
    emojis = settings.action_emojis

    lines = [f"{emojis.get(a, '🔹')} {a.capitalize()}" for a in actions]
    text = f"📋 <b>Доступные действия ({len(actions)}):</b>\n\n" + "\n".join(lines)

    await message.answer(text[:4000], parse_mode="HTML")


@router.message(F.text == "📖 Помощь")
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ <b>Помощь</b>\n\n"
        "Бот помогает выражать эмоции в чатах.\n"
        "Просто введите <code>@CuteForCutebot</code> в любом чате!",
        parse_mode="HTML",
    )


@router.message(F.text == "📊 Моя статистика")
@router.message(Command("stats"))
async def cmd_stats(message: Message, user_repo: UserRepository):
    user_service = UserService(user_repo)
    stats = await user_service.get_user_stats(message.from_user.id)
    text = format_stats_message(message.from_user.full_name, stats)
    await message.answer(text, parse_mode="HTML")
