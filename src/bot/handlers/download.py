"""Обработчики для скачивания исходников в формате Markdown."""

import datetime

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.states.activity import Download
from src.db import crud
from src.db.database import get_async_session
from src.db.models import ActivityType

router = Router()


@router.message(F.text == "Скачать исходники")
async def handle_download_start(message: types.Message, state: FSMContext):
    """Начинает процесс скачивания исходников."""
    await state.set_state(Download.waiting_for_start_date)
    await message.answer(
        "Введите дату начала периода в формате <b>ГГГГ-ММ-ДД</b>:"
    )


@router.message(Download.waiting_for_start_date)
async def handle_start_date(message: types.Message, state: FSMContext):
    """Обрабатывает введенную дату начала периода."""
    try:
        start_date = datetime.datetime.strptime(
            message.text, "%Y-%m-%d"
        ).date()
    except ValueError:
        await message.answer(
            "Неверный формат даты. Пожалуйста, введите дату "
            "в формате <b>ГГГГ-ММ-ДД</b>."
        )
        return

    await state.update_data(start_date=start_date)
    await state.set_state(Download.waiting_for_end_date)
    await message.answer(
        "Отлично! Теперь введите дату конца периода в формате "
        "<b>ГГГГ-ММ-ДД</b> (включительно)."
    )


@router.message(Download.waiting_for_end_date)
async def handle_end_date(message: types.Message, state: FSMContext):
    """Обрабатывает дату конца периода и отправляет файлы."""
    try:
        end_date = datetime.datetime.strptime(
            message.text, "%Y-%m-%d"
        ).date()
    except ValueError:
        await message.answer(
            "Неверный формат даты. Пожалуйста, введите дату "
            "в формате <b>ГГГГ-ММ-ДД</b>."
        )
        return

    user_data = await state.get_data()
    start_date = user_data["start_date"]

    if start_date > end_date:
        await message.answer(
            "Дата начала не может быть позже даты конца. "
            "Пожалуйста, начните процесс заново."
        )
        await state.clear()
        return

    await message.answer("Готовлю ваши файлы...")

    async for session in get_async_session():
        db: AsyncSession = session
        all_activities = await crud.get_all_activities(db)
        logs = await crud.get_logs_for_period(db, start_date, end_date)

        # Группируем логи по датам
        grouped_logs = {}
        for log in logs:
            if log.date not in grouped_logs:
                grouped_logs[log.date] = {}
            grouped_logs[log.date][log.activity_id] = log
        
        # Генерируем и отправляем файлы
        current_date = start_date
        while current_date <= end_date:
            daily_logs = grouped_logs.get(current_date, {})
            
            # Формируем контент файла
            md_content = f"Заголовок:\n{current_date.strftime('%Y-%m-%d')}\nДанные:\n---\n"
            for activity in all_activities:
                log = daily_logs.get(activity.id)
                if activity.type == ActivityType.CHECKBOX:
                    value = log.value_bool if log and log.value_bool is not None else False
                else:  # time
                    value = (
                        log.value_minutes
                        if log and log.value_minutes is not None
                        else 0
                    )
                md_content += f"{activity.name}: {value}\n"
            md_content += "---"
            
            # Отправляем файл
            file_to_send = BufferedInputFile(
                md_content.encode("utf-8"),
                filename=f"{current_date.strftime('%Y-%m-%d')}.md",
            )
            await message.answer_document(file_to_send)
            
            current_date += datetime.timedelta(days=1)

    await state.clear()
    await message.answer("Все готово!")
