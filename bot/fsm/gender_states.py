"""
FSM состояния для процесса выбора и изменения пола
"""

from aiogram.fsm.state import State, StatesGroup


class GenderSelectionStates(StatesGroup):
    """Состояния для выбора/изменения пола"""

    # Первый выбор пола (при регистрации)
    choosing_gender = State()

    # Подтверждение изменения пола
    confirming_gender_change = State()

    # Ввод причины изменения (опционально)
    entering_reason = State()
