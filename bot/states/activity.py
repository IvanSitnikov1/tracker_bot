"""Модуль для определения состояний FSM."""

from aiogram.fsm.state import State, StatesGroup


class AddActivity(StatesGroup):
    """Состояния для процесса добавления новой активности."""
    waiting_for_name = State()
    choosing_type = State()


class TrackActivity(StatesGroup):
    """Состояния для отслеживания активностей."""
    running_timers = State()
    waiting_for_manual_time = State()


class Download(StatesGroup):
    """Состояния для процесса скачивания исходников."""
    choosing_start_date = State()
    choosing_end_date = State()

