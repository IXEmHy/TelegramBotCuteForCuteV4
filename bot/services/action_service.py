"""Сервис для работы с действиями из actions.json"""

import json
from pathlib import Path
from typing import Optional, List, Dict
from functools import lru_cache


class ActionService:
    """Сервис для работы с действиями бота"""

    def __init__(self):
        self.actions_path = Path(__file__).parent.parent / "data" / "actions.json"
        self._actions_data = None

    @property
    def actions_data(self) -> dict:
        """Ленивая загрузка данных о действиях"""
        if self._actions_data is None:
            self._load_actions()
        return self._actions_data

    def _load_actions(self):
        """Загрузить действия из JSON файла"""
        try:
            with open(self.actions_path, "r", encoding="utf-8") as f:
                self._actions_data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл actions.json не найден: {self.actions_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON: {e}")

    def get_all_actions(self) -> List[Dict]:
        """Получить все действия"""
        return self.actions_data.get("actions", [])

    def get_action_by_id(self, action_id: int) -> Optional[Dict]:
        """
        Получить действие по ID

        Args:
            action_id: ID действия

        Returns:
            Словарь с данными действия или None
        """
        for action in self.get_all_actions():
            if action["id"] == action_id:
                return action
        return None

    def get_action_by_name(self, action_name: str) -> Optional[Dict]:
        """
        Получить действие по названию

        Args:
            action_name: Название действия

        Returns:
            Словарь с данными действия или None
        """
        for action in self.get_all_actions():
            if action["name"].lower() == action_name.lower():
                return action
        return None

    def get_actions_by_category(self, category: str) -> List[Dict]:
        """
        Получить действия по категории

        Args:
            category: Категория действий

        Returns:
            Список действий в категории
        """
        return [
            action
            for action in self.get_all_actions()
            if action.get("category") == category
        ]

    def get_inline_text(self, action_id: int, user1_name: str) -> str:
        """
        Получить текст для inline-запроса

        Args:
            action_id: ID действия
            user1_name: Имя отправителя

        Returns:
            Форматированный текст
        """
        action = self.get_action_by_id(action_id)
        if not action:
            return ""

        return action["inline_text"].format(user1=user1_name)

    def get_accepted_text(
        self, action_id: int, user1_name: str, user2_name: str, user1_gender: str
    ) -> str:
        """
        Получить текст при принятии действия

        Args:
            action_id: ID действия
            user1_name: Имя отправителя
            user2_name: Имя получателя
            user1_gender: Пол отправителя ('male' или 'female')

        Returns:
            Форматированный текст
        """
        action = self.get_action_by_id(action_id)
        if not action:
            return ""

        gender = user1_gender if user1_gender in ["male", "female"] else "male"
        text_template = action["accepted"].get(gender, action["accepted"]["male"])

        return text_template.format(user1=user1_name, user2=user2_name)

    def get_rejected_text(
        self, action_id: int, user2_name: str, user2_gender: str
    ) -> str:
        """
        Получить текст при отказе от действия

        Args:
            action_id: ID действия
            user2_name: Имя получателя
            user2_gender: Пол получателя ('male' или 'female')

        Returns:
            Форматированный текст
        """
        action = self.get_action_by_id(action_id)
        if not action:
            return ""

        gender = user2_gender if user2_gender in ["male", "female"] else "male"
        text_template = action["rejected"].get(gender, action["rejected"]["male"])

        return text_template.format(user2=user2_name)

    def get_action_emoji(self, action_id: int) -> str:
        """Получить emoji действия"""
        action = self.get_action_by_id(action_id)
        return action.get("emoji", "❓") if action else "❓"

    def search_actions(self, query: str) -> List[Dict]:
        """
        Поиск действий по запросу

        Args:
            query: Поисковый запрос

        Returns:
            Список найденных действий
        """
        query = query.lower()
        results = []

        for action in self.get_all_actions():
            if query in action["name"].lower():
                results.append(action)

        return results


# Глобальный экземпляр сервиса
action_service = ActionService()
