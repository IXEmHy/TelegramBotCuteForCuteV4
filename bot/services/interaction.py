"""
Сервис для работы с взаимодействиями

Содержит бизнес-логику:
- Создание взаимодействий
- Обработка ответов (принять/отклонить)
- Получение истории
"""

from typing import Optional
import logging

from bot.database.repositories import InteractionRepository
from bot.database.models import Interaction, InteractionStatus
from bot.utils.validators import can_interact_with_user, is_valid_action

logger = logging.getLogger(__name__)


class InteractionService:
    """Сервис для работы с взаимодействиями"""

    def __init__(self, interaction_repo: InteractionRepository):
        """
        Инициализация сервиса

        Args:
            interaction_repo: Репозиторий взаимодействий
        """
        self.interaction_repo = interaction_repo

    async def create_interaction(
        self,
        sender_id: int,
        receiver_id: int,
        action: str,
        message_id: Optional[int] = None,
    ) -> tuple[Optional[Interaction], Optional[str]]:
        """
        Создает новое взаимодействие

        Args:
            sender_id: ID отправителя
            receiver_id: ID получателя
            action: Название действия
            message_id: ID сообщения в Telegram

        Returns:
            tuple[Optional[Interaction], Optional[str]]:
                (взаимодействие, сообщение об ошибке)
        """
        # Валидация
        can_interact, error_msg = can_interact_with_user(sender_id, receiver_id)
        if not can_interact:
            return None, error_msg

        if not is_valid_action(action):
            return None, f"❌ Недопустимое действие: {action}"

        # Создание
        try:
            interaction = await self.interaction_repo.create(
                sender_id=sender_id,
                receiver_id=receiver_id,
                action=action,
                message_id=message_id,
            )
            logger.info(
                f"Создано взаимодействие #{interaction.id}: "
                f"{sender_id} -> {receiver_id} ({action})"
            )
            return interaction, None
        except Exception as e:
            logger.error(f"Ошибка создания взаимодействия: {e}")
            return None, "❌ Ошибка при создании взаимодействия"

    async def respond_to_interaction(
        self, interaction_id: int, accept: bool
    ) -> tuple[bool, str]:
        """
        Обрабатывает ответ на взаимодействие

        Args:
            interaction_id: ID взаимодействия
            accept: True для принятия, False для отклонения

        Returns:
            tuple[bool, str]: (успех, сообщение)
        """
        # Получаем взаимодействие
        interaction = await self.interaction_repo.get_by_id(interaction_id)

        if not interaction:
            return False, "❌ Взаимодействие не найдено"

        # Проверяем статус
        if interaction.status != InteractionStatus.PENDING:
            return False, "❌ На это взаимодействие уже дан ответ"

        # Обновляем статус
        new_status = (
            InteractionStatus.ACCEPTED if accept else InteractionStatus.DECLINED
        )
        success = await self.interaction_repo.update_status(interaction_id, new_status)

        if success:
            action_text = "принято" if accept else "отклонено"
            logger.info(f"Взаимодействие #{interaction_id} {action_text}")
            return True, ""
        else:
            return False, "❌ Ошибка при обновлении статуса"

    async def get_interaction(self, interaction_id: int) -> Optional[Interaction]:
        """
        Получает взаимодействие по ID

        Args:
            interaction_id: ID взаимодействия

        Returns:
            Optional[Interaction]: Взаимодействие или None
        """
        return await self.interaction_repo.get_by_id(interaction_id)

    async def get_user_recent_interactions(
        self, user_id: int, limit: int = 10
    ) -> list[Interaction]:
        """
        Получает последние взаимодействия пользователя

        Args:
            user_id: ID пользователя
            limit: Количество записей

        Returns:
            list[Interaction]: Список взаимодействий
        """
        return await self.interaction_repo.get_user_recent_interactions(user_id, limit)
