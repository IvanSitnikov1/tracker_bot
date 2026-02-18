"""Модуль с inline-клавиатурами."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.db.models import Activity, ActivityLog, ActivityType


def get_activity_type_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для выбора типа активности."""
    buttons = [
        [
            InlineKeyboardButton(text="☑️ Checkbox", callback_data="add_activity:checkbox"),
            InlineKeyboardButton(text="⏱️ Time", callback_data="add_activity:time"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def get_activities_keyboard(
    activities: list[Activity],
    today_logs: dict[int, ActivityLog],
    running_timers: dict[int, int],
) -> InlineKeyboardMarkup:
    """
    Создает и возвращает клавиатуру со списком активностей.
    
    Args:
        activities: Список объектов Activity.
        today_logs: Словарь с логами за сегодня, где ключ - ID активности.
        running_timers: Словарь с запущенными таймерами {activity_id: start_timestamp}.
    """
    buttons = []
    for activity in activities:
        log = today_logs.get(activity.id)
        
        if activity.type == ActivityType.CHECKBOX:
            status_icon = "✅" if log and log.value_bool else "☑️"
            button_text = f"{status_icon} {activity.name}"
        
        elif activity.type == ActivityType.TIME:
            is_running = activity.id in running_timers
            status_icon = "⏹️" if is_running else "▶️"
            total_minutes = log.value_minutes if log and log.value_minutes else 0
            button_text = f"{status_icon} {activity.name} ({total_minutes} мин.)"
            
        else:
            button_text = activity.name

        callback_data = f"track:{activity.id}"
        buttons.append(
            [InlineKeyboardButton(text=button_text, callback_data=callback_data)]
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_stats_period_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для выбора периода статистики."""
    buttons = [
        [
            InlineKeyboardButton(text="За сегодня", callback_data="stats:day"),
            InlineKeyboardButton(text="За неделю", callback_data="stats:week"),
            InlineKeyboardButton(text="За месяц", callback_data="stats:month"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
