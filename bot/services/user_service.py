"""Сервис для работы с пользователями"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from bot.database.models import User


class UserService:
    """Сервис для работы с пользователями"""

    @staticmethod
    def get_or_create_user(
        session: Session,
        user_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> User:
        """
        Получить существующего пользователя или создать нового

        Args:
            session: Сессия БД
            user_id: Telegram ID пользователя
            username: Username пользователя
            full_name: Полное имя пользователя

        Returns:
            Объект User
        """
        user = session.query(User).filter(User.user_id == user_id).first()

        if not user:
            user = User(
                user_id=user_id,
                username=username,
                full_name=full_name,
                gender=None,  # Будет установлен при выборе
                gender_changes_count=0,
                last_gender_change=None,
            )
            session.add(user)
            session.commit()
        else:
            # Обновляем информацию, если изменилась
            if username and user.username != username:
                user.username = username
            if full_name and user.full_name != full_name:
                user.full_name = full_name
            session.commit()

        return user

    @staticmethod
    def set_gender(
        session: Session, user_id: int, gender: str, is_first_time: bool = False
    ) -> bool:
        """
        Установить пол пользователя

        Args:
            session: Сессия БД
            user_id: ID пользователя
            gender: Пол ('male' или 'female')
            is_first_time: Первый выбор (при регистрации)

        Returns:
            True если успешно, False если превышен лимит
        """
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return False

        # Первый выбор - всегда разрешён
        if user.gender is None or is_first_time:
            user.gender = gender
            user.last_gender_change = datetime.now()
            session.commit()
            return True

        # Проверяем лимит изменений
        if not UserService.can_change_gender(session, user_id):
            return False

        user.gender = gender
        user.gender_changes_count += 1
        user.last_gender_change = datetime.now()
        session.commit()
        return True

    @staticmethod
    def can_change_gender(session: Session, user_id: int) -> bool:
        """
        Проверить, может ли пользователь изменить пол

        Args:
            session: Сессия БД
            user_id: ID пользователя

        Returns:
            True если может, False если нет
        """
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return False

        # Первый выбор - всегда разрешён
        if user.gender is None:
            return True

        # Проверяем прошло ли 30 дней с последнего изменения
        if user.last_gender_change:
            days_passed = (datetime.now() - user.last_gender_change).days
            if days_passed >= 30:
                # Сбрасываем счётчик
                user.gender_changes_count = 0
                session.commit()

        # Проверяем лимит (3 раза в месяц)
        return user.gender_changes_count < 3

    @staticmethod
    def get_remaining_gender_changes(session: Session, user_id: int) -> int:
        """
        Получить количество оставшихся изменений пола

        Args:
            session: Сессия БД
            user_id: ID пользователя

        Returns:
            Количество оставшихся изменений
        """
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user or user.gender is None:
            return 3

        # Проверяем прошло ли 30 дней
        if user.last_gender_change:
            days_passed = (datetime.now() - user.last_gender_change).days
            if days_passed >= 30:
                return 3

        return max(0, 3 - user.gender_changes_count)

    @staticmethod
    def get_user_gender(session: Session, user_id: int) -> Optional[str]:
        """
        Получить пол пользователя

        Args:
            session: Сессия БД
            user_id: ID пользователя

        Returns:
            'male', 'female' или None
        """
        user = session.query(User).filter(User.user_id == user_id).first()
        return user.gender if user else None

    @staticmethod
    def get_user_display_name(session: Session, user_id: int) -> str:
        """
        Получить отображаемое имя пользователя

        Args:
            session: Сессия БД
            user_id: ID пользователя

        Returns:
            Имя пользователя (full_name или username или "Пользователь")
        """
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return "Пользователь"

        return user.full_name or user.username or "Пользователь"
