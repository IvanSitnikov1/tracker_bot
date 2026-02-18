"""Обработчики для скачивания исходников в формате Markdown с помощью календаря."""

import datetime

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import inline as inline_kb
from src.bot.keyboards.callback_data import CalendarCallback
from src.bot.states.activity import Download
from src.db import crud
from src.db.database import get_async_session
from src.db.models import ActivityType

router = Router()


@router.message(F.text == "Скачать исходники")
async def handle_download_start(message: types.Message, state: FSMContext):
    """Начинает процесс скачивания исходников, показывая календарь."""
    await state.set_state(Download.choosing_start_date)
    today = datetime.date.today()
    keyboard = await inline_kb.create_calendar_keyboard(today.year, today.month)
    await message.answer(
        "Выберите дату начала периода:", reply_markup=keyboard
    )


@router.callback_query(CalendarCallback.filter(F.action == "NAV"))
async def handle_calendar_navigation(
    callback: types.CallbackQuery, callback_data: CalendarCallback
):
    """Обрабатывает навигацию по календарю (смена месяца)."""
    keyboard = await inline_kb.create_calendar_keyboard(
        year=callback_data.year, month=callback_data.month
    )
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(CalendarCallback.filter(F.action == "DAY"))
async def handle_day_selection(
    callback: types.CallbackQuery,
    callback_data: CalendarCallback,
    state: FSMContext,
):
    """Обрабатывает выбор дня в календаре."""
    current_state = await state.get_state()
    selected_date = datetime.date(
        year=callback_data.year,
        month=callback_data.month,
        day=callback_data.day,
    )

    if current_state == Download.choosing_start_date:
        await state.update_data(start_date=selected_date)
        await state.set_state(Download.choosing_end_date)
        await callback.message.edit_text(
            f"Выбрана дата начала: <b>{selected_date.strftime('%d.%m.%Y')}</b>\n\n"
            "Теперь выберите дату конца периода:",
            reply_markup=callback.message.reply_markup, # Оставляем тот же календарь
        )
    
    elif current_state == Download.choosing_end_date:
        user_data = await state.get_data()
        start_date = user_data["start_date"]
        end_date = selected_date

        if start_date > end_date:
            await callback.answer(
                "Дата конца не может быть раньше даты начала!", show_alert=True
            )
            return

        await state.clear()
        await callback.message.edit_text(f"Готовлю файлы за период с "
                                          f"<b>{start_date.strftime('%d.%m.%Y')}</b> по "
                                          f"<b>{end_date.strftime('%d.%m.%Y')}</b>...")
        
        # Запускаем генерацию и отправку файлов
        await generate_and_send_files(callback.message, start_date, end_date)

    await callback.answer()


async def generate_and_send_files(
    message: types.Message, start_date: datetime.date, end_date: datetime.date
):
    """Генерирует и отправляет файлы с логами за указанный период."""
    async for session in get_async_session():
        db: AsyncSession = session
        all_activities = await crud.get_all_activities(db)
        logs = await crud.get_logs_for_period(db, start_date, end_date)

        grouped_logs = {}
        for log in logs:
            if log.date not in grouped_logs:
                grouped_logs[log.date] = {}
            grouped_logs[log.date][log.activity_id] = log

        current_date = start_date
        while current_date <= end_date:
            daily_logs = grouped_logs.get(current_date, {})
            md_content = f"---\n"
            for activity in all_activities:
                log = daily_logs.get(activity.id)
                value = 0
                if log:
                    if activity.type == ActivityType.CHECKBOX:
                        value = log.value_bool if log.value_bool is not None else False
                    elif activity.type == ActivityType.TIME:
                        value = log.value_minutes if log.value_minutes is not None else 0
                md_content += f"{activity.name}: {value}\n"
            md_content += "---"

            file_to_send = BufferedInputFile(
                md_content.encode("utf-8"),
                filename=f"{current_date.strftime('%Y-%m-%d')}.md",
            )
            await message.answer_document(file_to_send)
            current_date += datetime.timedelta(days=1)

    await message.answer("Все готово!")
