"""Обработчики для просмотра статистики."""

import datetime

from aiogram import Router, F, types
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import inline as inline_kb
from db import crud
from db.database import get_async_session
from db.models import ActivityType

router = Router()


@router.message(F.text == "Просмотр статистики")
async def handle_stats_start(message: types.Message):
    """Начинает процесс просмотра статистики."""
    keyboard = inline_kb.get_stats_period_keyboard()
    await message.answer(
        "Выберите период для просмотра статистики:", reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("stats:"))
async def handle_stats_period(callback: types.CallbackQuery):
    """Обрабатывает выбор периода и показывает статистику."""
    period = callback.data.split(":")[1]
    today = datetime.date.today()

    if period == "day":
        start_date = today
        end_date = today
        period_text = "за сегодня"
    elif period == "week":
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = start_date + datetime.timedelta(days=6)
        period_text = "за текущую неделю"
    elif period == "month":
        start_date = today.replace(day=1)
        end_date = (start_date + datetime.timedelta(days=31)).replace(
            day=1
        ) - datetime.timedelta(days=1)
        period_text = "за текущий месяц"
    else:
        return

    async for session in get_async_session():
        db: AsyncSession = session
        stats = await crud.get_stats_for_period(db, start_date, end_date)

        if not stats:
            await callback.message.edit_text(
                f"Нет данных для статистики {period_text}."
            )
            await callback.answer()
            return

        response_text = f"📊 <b>Статистика {period_text}:</b>\n\n"
        for name, type, total_minutes, total_checks in stats:
            if type == ActivityType.CHECKBOX:
                response_text += f"☑️ {name}: отмечено {total_checks or 0} раз\n"
            elif type == ActivityType.TIME:
                response_text += f"⏱️ {name}: {total_minutes or 0} мин.\n"
        
        await callback.message.edit_text(response_text)
    
    await callback.answer()
