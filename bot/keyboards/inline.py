"""Модуль с inline-клавиатурами."""
import calendar

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.callback_data import ActivityCallback, CalendarCallback
from db.models import Activity, ActivityLog, ActivityType


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
        button_row = []
        
        if activity.type == ActivityType.CHECKBOX:
            status_icon = "✅" if log and log.value_bool else "☑️"
            button_text = f"{status_icon} {activity.name}"
            callback_data = ActivityCallback(action="track", activity_id=activity.id).pack()
            button_row.append(
                InlineKeyboardButton(text=button_text, callback_data=callback_data)
            )

        elif activity.type == ActivityType.TIME:
            is_running = activity.id in running_timers
            status_icon = "⏹️" if is_running else "▶️"
            total_minutes = log.value_minutes if log and log.value_minutes else 0
            button_text = f"{status_icon} {activity.name} ({total_minutes} мин.)"
            
            # Кнопка для старт/стоп
            button_row.append(InlineKeyboardButton(
                text=button_text,
                callback_data=ActivityCallback(action="track", activity_id=activity.id).pack()
            ))
            # Кнопка для ручного ввода
            button_row.append(InlineKeyboardButton(
                text="✏️",
                callback_data=ActivityCallback(action="manual_time", activity_id=activity.id).pack()
            ))
            
        else:
            button_text = activity.name
            callback_data = ActivityCallback(action="track", activity_id=activity.id).pack()
            button_row.append(
                InlineKeyboardButton(text=button_text, callback_data=callback_data)
            )

        buttons.append(button_row)
    
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


async def create_calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    """Создает inline-клавиатуру с календарем на указанный месяц и год."""
    
    # Названия месяцев на русском
    month_names = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]

    # Создаем клавиатуру
    inline_keyboard = []

    # Первая строка: Название месяца и год
    month_str = month_names[month - 1]
    inline_keyboard.append([
        InlineKeyboardButton(
            text=f"{month_str} {year}",
            callback_data="calendar_ignore" # Пустышка
        )
    ])

    # Вторая строка: Дни недели
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    inline_keyboard.append(
        [InlineKeyboardButton(text=day, callback_data="calendar_ignore") for day in week_days]
    )

    # Строки с датами
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="calendar_ignore"))
            else:
                row.append(InlineKeyboardButton(
                    text=str(day),
                    callback_data=CalendarCallback(action="DAY", year=year, month=month, day=day).pack()
                ))
        inline_keyboard.append(row)

    # Последняя строка: Навигация
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year += 1
        
    inline_keyboard.append([
        InlineKeyboardButton(
            text="<",
            callback_data=CalendarCallback(action="NAV", year=prev_year, month=prev_month).pack()
        ),
        InlineKeyboardButton(text=" ", callback_data="calendar_ignore"),
        InlineKeyboardButton(
            text=">",
            callback_data=CalendarCallback(action="NAV", year=next_year, month=next_month).pack()
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
