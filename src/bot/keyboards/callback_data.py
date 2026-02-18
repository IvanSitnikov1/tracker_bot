"""Модуль для фабрик CallbackData."""

from aiogram.filters.callback_data import CallbackData


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
