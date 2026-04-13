"""Обработчики для просмотра статистики."""

import datetime

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import inline as inline_kb
from bot.keyboards.callback_data import CalendarCallback
from bot.states.activity import Stats
from db import crud
from db.database import get_async_session
from db.models import ActivityType

router = Router()


async def show_stats_for_period(
    message: types.Message,
    user_id: int,
    start_date: datetime.date,
    end_date: datetime.date,
    period_text: str,
):
    """Отображает статистику за указанный период."""
    async for session in get_async_session():
        db: AsyncSession = session
        stats = await crud.get_user_stats_for_period(
            db, user_id=user_id, start_date=start_date, end_date=end_date
        )

        if not stats:
            await message.edit_text(f"Нет данных для статистики {period_text}.")
            return

        response_text = f"📊 <b>Статистика {period_text}:</b>\n\n"
        for name, type, total_minutes, total_checks in stats:
            if type == ActivityType.CHECKBOX:
                response_text += f"☑️ {name}: отмечено {total_checks or 0} раз\n"
            elif type == ActivityType.TIME:
                response_text += f"⏱️ {name}: {total_minutes or 0} мин.\n"

        await message.edit_text(response_text)


@router.message(F.text == "Просмотр статистики")
async def handle_stats_start(message: types.Message):
    """Начинает процесс просмотра статистики."""
    keyboard = inline_kb.get_stats_period_keyboard()
    await message.answer("Выберите период для просмотра статистики:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("stats:"))
async def handle_stats_period(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает выбор периода и показывает статистику."""
    await callback.answer()
    user_id = callback.from_user.id
    period = callback.data.split(":")[1]
    today = datetime.date.today()

    if period == "day":
        start_date = end_date = today
        period_text = "за сегодня"
        await show_stats_for_period(
            callback.message, user_id, start_date, end_date, period_text
        )
    elif period == "week":
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = start_date + datetime.timedelta(days=6)
        period_text = "за текущую неделю"
        await show_stats_for_period(
            callback.message, user_id, start_date, end_date, period_text
        )
    elif period == "month":
        start_date = today.replace(day=1)
        end_date = (start_date + datetime.timedelta(days=31)).replace(
            day=1
        ) - datetime.timedelta(days=1)
        period_text = "за текущий месяц"
        await show_stats_for_period(
            callback.message, user_id, start_date, end_date, period_text
        )
    elif period == "custom":
        await state.set_state(Stats.choosing_start_date)
        keyboard = await inline_kb.create_calendar_keyboard(today.year, today.month)
        await callback.message.edit_text(
            "Выберите дату начала периода:", reply_markup=keyboard
        )


@router.callback_query(Stats.choosing_start_date, CalendarCallback.filter(F.action == "NAV"))
@router.callback_query(Stats.choosing_end_date, CalendarCallback.filter(F.action == "NAV"))
async def handle_stats_calendar_navigation(
    callback: types.CallbackQuery, callback_data: CalendarCallback
):
    """Обрабатывает навигацию по календарю в режиме статистики."""
    keyboard = await inline_kb.create_calendar_keyboard(
        year=callback_data.year, month=callback_data.month
    )
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(
    CalendarCallback.filter(F.action == "DAY"),
    StateFilter(Stats.choosing_start_date, Stats.choosing_end_date),
)
async def handle_stats_day_selection(
    callback: types.CallbackQuery,
    callback_data: CalendarCallback,
    state: FSMContext,
):
    """Обрабатывает выбор дня в календаре для статистики."""
    await callback.answer()
    current_state = await state.get_state()

    user_id = callback.from_user.id
    selected_date = datetime.date(
        year=callback_data.year,
        month=callback_data.month,
        day=callback_data.day,
    )

    if current_state == Stats.choosing_start_date:
        await state.update_data(start_date=selected_date)
        await state.set_state(Stats.choosing_end_date)
        await callback.message.edit_text(
            f"Выбрана дата начала: <b>{selected_date.strftime('%d.%m.%Y')}</b>\n\n"
            "Теперь выберите дату конца периода:",
            reply_markup=callback.message.reply_markup,
        )

    elif current_state == Stats.choosing_end_date:
        user_data = await state.get_data()
        start_date = user_data["start_date"]
        end_date = selected_date

        if start_date > end_date:
            await callback.answer(
                "Дата конца не может быть раньше даты начала!", show_alert=True
            )
            return

        await state.clear()
        period_text = (
            f"c {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}"
        )
        await show_stats_for_period(
            callback.message, user_id, start_date, end_date, period_text
        )
