"""Модуль для определения состояний FSM."""

from aiogram.fsm.state import State, StatesGroup


class AddActivity(StatesGroup):
    """Состояния для процесса добавления новой активности."""
    waiting_for_name = State()
    choosing_type = State()


class TrackActivity(StatesGroup):
    """Состояния для отслеживания активностей."""
    running_timers = State()


class Download(StatesGroup):
    """Состояния для процесса скачивания исходников."""
    waiting_for_start_date = State()
    waiting_for_end_date = State()

