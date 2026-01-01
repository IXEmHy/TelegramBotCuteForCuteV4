"""
FSM состояния для админ-панели
"""

from aiogram.fsm.state import State, StatesGroup


class ActionAddStates(StatesGroup):
    """Состояния для добавления действия"""

    waiting_for_name = State()
    waiting_for_emoji = State()
    waiting_for_infinitive = State()
    waiting_for_past = State()
    waiting_for_noun = State()


class BroadcastStates(StatesGroup):
    """Состояния для рассылки"""

    waiting_for_message = State()
