"""Модуль для фабрик CallbackData."""

from aiogram.filters.callback_data import CallbackData


class ActivityCallback(CallbackData, prefix="activity"):
    """
    CallbackData для действий с активностями.

    - action: 'track' (старт/стоп), 'manual_time' (ручной ввод)
    - activity_id: ID активности
    """
    action: str
    activity_id: int


class CalendarCallback(CallbackData, prefix="calendar"):
    """
    CallbackData для навигации по календарю и выбора даты.
    
    - action: 'NAV' (навигация), 'DAY' (выбор дня)
    - year: год
    - month: месяц
    - day: день (опционально, для action='DAY')
    """
    action: str
    year: int
    month: int
    day: int | None = None
