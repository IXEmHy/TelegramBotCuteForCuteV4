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
            await callback.answer()  # Пустой ответ, без уведомления
            return

        sender_id = int(parts[1])
        action_id = int(parts[2])
        is_accept = parts[3] == "1"

        receiver = callback.from_user

        # Проверка: нельзя принять своё же действие
        if sender_id == receiver.id:
            await callback.answer()
            return

        # Получаем данные действия из БД
        action_data = await action_repo.get_by_id(action_id)
        if not action_data:
            await callback.answer()
            if callback.message:
                try:
                    await callback.message.delete()
                except Exception:
                    pass
            return

        # Извлекаем данные действия
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
            await callback.answer()
            return

        await user_service.register_or_update_user(receiver)

        # Получаем message_id если доступен
        message_id = callback.message.message_id if callback.message else None

        # Создаём запись взаимодействия
        interaction, error = await interaction_service.create_interaction(
            sender_id=sender_id,
            receiver_id=receiver.id,
            action=action_name,
            message_id=message_id,
        )

        if not interaction:
            logger.error(f"Failed to create interaction: {error}")
            await callback.answer()
            return

        # Обновляем статус через respond_to_interaction
        success, error_msg = await interaction_service.respond_to_interaction(
            interaction_id=interaction.id, accept=is_accept
        )

        if not success:
            logger.warning(f"Failed to update interaction status: {error_msg}")

        # Обновляем статистику действий
        await action_stat_repo.increment_received(receiver.id, action_name)

        if is_accept:
            await action_stat_repo.increment_accepted(receiver.id, action_name)
        else:
            await action_stat_repo.increment_declined(receiver.id, action_name)

        # Формируем ответное сообщение
        # Используем полное имя пользователя
        sender_name = sender.full_name
        receiver_name = receiver.full_name

        if is_accept:
            # Формат: {sender} {past_tense} {receiver} {emoji}
            new_text = f"{sender_name} {past_tense} {receiver_name} {emoji}"
        else:
            # Формат: {receiver} отказался от {genitive_noun} ❌
            new_text = f"{receiver_name} отказался от {genitive_noun} ❌"

        # ВАЖНО: Отвечаем на callback БЕЗ текста (убираем часики загрузки)
        await callback.answer()

        # Обновляем сообщение (убираем кнопки, меняем текст)
        if callback.message:
            try:
                logger.debug(f"Editing message: {new_text}")
                await callback.message.edit_text(
                    text=new_text,
                    reply_markup=None,  # Убираем кнопки
                )
                logger.debug("Message edited successfully")
            except Exception as e:
                logger.error(f"⚠️ Не удалось обновить сообщение: {e}", exc_info=True)
        else:
            logger.warning("Callback.message is None - cannot edit")

    except Exception as e:
        logger.error(f"❌ Error in interaction callback: {e}", exc_info=True)
        # Даже при ошибке отвечаем на callback
        try:
            await callback.answer()
        except Exception:
            pass
