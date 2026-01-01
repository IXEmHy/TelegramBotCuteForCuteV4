"""
Обработчик callback запросов (нажатия на кнопки)
"""

import logging
from aiogram import Router
from aiogram.types import CallbackQuery

from bot.database.models import InteractionStatus
from bot.database.repositories import (
    UserRepository,
    InteractionRepository,
    ActionRepository,
    ActionStatRepository,
)
from bot.services.user import UserService
from bot.services.interaction import InteractionService

logger = logging.getLogger(__name__)

router = Router(name="callbacks")


@router.callback_query(lambda c: c.data.startswith("iact:"))
async def handle_interaction_callback(
    callback: CallbackQuery,
    user_repo: UserRepository,
    interaction_repo: InteractionRepository,
    action_repo: ActionRepository,
    action_stat_repo: ActionStatRepository,
):
    """
    Обработка нажатий на кнопки Принять/Отказаться для взаимодействий.

    Формат callback_data: iact:{sender_id}:{action_id}:{accept=1/0}
    """
    try:
        # Парсим callback data
        parts = callback.data.split(":")
        if len(parts) != 4:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("❌ Ошибка данных", show_alert=True)
            return

        sender_id = int(parts[1])
        action_id = int(parts[2])
        is_accept = parts[3] == "1"

        receiver = callback.from_user

        # Проверка: нельзя принять своё же действие
        if sender_id == receiver.id:
            await callback.answer(
                "❌ Нельзя взаимодействовать с самим собой!", show_alert=True
            )
            return

        # Получаем данные действия из БД (теперь это dict)
        action_data = await action_repo.get_by_id(action_id)
        if not action_data:
            await callback.answer("❌ Действие больше не доступно", show_alert=True)
            # Пытаемся удалить сообщение если оно есть
            if callback.message:
                try:
                    await callback.message.delete()
                except Exception:
                    pass
            return

        # Извлекаем данные действия для сообщения (dict, не объект!)
        action_name = action_data["name"]
        emoji = action_data["emoji"]
        past_tense = action_data["past_tense"]
        genitive_noun = action_data["genitive_noun"]

        # Инициализируем сервисы
        user_service = UserService(user_repo)
        interaction_service = InteractionService(interaction_repo)

        # Регистрируем/обновляем пользователей
        sender = await user_repo.get_by_id(sender_id)
        if not sender:
            await callback.answer("❌ Отправитель не найден", show_alert=True)
            return

        await user_service.register_or_update_user(receiver)

        # Определяем статус
        status = InteractionStatus.ACCEPTED if is_accept else InteractionStatus.DECLINED

        # Получаем message_id если доступен (может быть None в inline режиме)
        message_id = callback.message.message_id if callback.message else None

        # Создаём запись взаимодействия
        await interaction_service.create_interaction(
            sender_id=sender_id,
            receiver_id=receiver.id,
            action=action_name,
            status=status,
            message_id=message_id,
        )

        # Обновляем статистику действий
        await action_stat_repo.increment_received(receiver.id, action_name)

        if is_accept:
            await action_stat_repo.increment_accepted(receiver.id, action_name)
        else:
            await action_stat_repo.increment_declined(receiver.id, action_name)

        # Формируем ответное сообщение
        sender_link = f"[{sender.full_name}](tg://user?id={sender.id})"
        receiver_link = f"[{receiver.full_name}](tg://user?id={receiver.id})"

        if is_accept:
            new_text = f"{emoji} {sender_link} {past_tense} {receiver_link}"
            toast_text = "✅ Принято!"
        else:
            new_text = (
                f"❌ {receiver_link} отказался от {genitive_noun} от {sender_link}"
            )
            toast_text = "❌ Отказано"

        # Показываем уведомление
        await callback.answer(toast_text, show_alert=False)

        # Обновляем сообщение (убираем кнопки, меняем текст)
        # ВАЖНО: проверяем наличие callback.message
        if callback.message:
            try:
                await callback.message.edit_text(
                    text=new_text, parse_mode="Markdown", reply_markup=None
                )
            except Exception as e:
                logger.warning(f"⚠️ Не удалось обновить сообщение callback: {e}")
        else:
            logger.debug("Callback без привязки к сообщению (inline режим)")

    except Exception as e:
        logger.error(f"❌ Error in interaction callback: {e}", exc_info=True)
        await callback.answer("❌ Произошла системная ошибка", show_alert=True)
