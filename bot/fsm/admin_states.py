"""
Состояния FSM для админ-панели
"""

from aiogram.fsm.state import State, StatesGroup


class ActionAddStates(StatesGroup):
    """Состояния добавления нового действия"""

    waiting_for_name = State()  # Название (например: "Обнять")
    waiting_for_emoji = State()  # Эмодзи
    waiting_for_infinitive = State()  # Инфинитив (что сделать? обнять)
    waiting_for_past = State()  # Прошедшее (что сделал? обнял)
    waiting_for_noun = State()  # Родительный (кого/чего? объятия)
    confirm = State()  # Подтверждение


class ActionEditStates(StatesGroup):
    """Состояния редактирования действия"""

    waiting_for_value = State()  # Новое значение поля
