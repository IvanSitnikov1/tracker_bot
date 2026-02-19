"""Обработчики для отображения и трекинга активностей."""
import datetime
import time

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import inline as inline_kb
from db import crud
from db.database import get_async_session
from db.models import ActivityType

router = Router()


async def _get_and_show_activities(
    user_id: int,
    state: FSMContext,
    db: AsyncSession,
    message: types.Message | None = None,
    callback: types.CallbackQuery | None = None,
):
    """Вспомогательная функция для получения и отображения активностей."""
    activities = await crud.get_user_activities(db, user_id=user_id)

    if not activities:
        answer_target = message or (callback.message if callback else None)
        if answer_target:
            await answer_target.answer(
                "У вас пока нет добавленных активностей. "
                "Нажмите 'Добавить активность', чтобы начать."
            )
        return

    today_logs = await crud.get_today_logs_for_user_activities(db, user_id=user_id)
    user_data = await state.get_data()
    running_timers = user_data.get("running_timers", {})

    keyboard = await inline_kb.get_activities_keyboard(
        activities, today_logs, running_timers
    )

    if message:
        await message.answer(
            "Выберите активность для отметки:",
            reply_markup=keyboard,
        )
    elif callback and callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except Exception:
            # Если сообщение не изменилось, просто игнорируем ошибку
            pass


@router.message(F.text == "Активности")
async def handle_activities_list(message: types.Message, state: FSMContext):
    """Отображает список всех активностей для трекинга."""
    if not message.from_user:
        return

    async for session in get_async_session():
        await _get_and_show_activities(
            user_id=message.from_user.id,
            state=state,
            db=session,
            message=message,
        )


@router.callback_query(F.data.startswith("track:"))
async def handle_track_callback(
    callback: types.CallbackQuery, state: FSMContext
):
    """Обрабатывает нажатие на кнопку активности."""
    user_id = callback.from_user.id
    activity_id = int(callback.data.split(":")[1])
    today = datetime.date.today()

    async for session in get_async_session():
        db: AsyncSession = session
        activity = await crud.get_activity_by_id(
            db, user_id=user_id, activity_id=activity_id
        )
        if not activity:
            await callback.answer("Активность не найдена!", show_alert=True)
            return

        # Получаем или создаем лог для сегодняшнего дня
        log = await crud.get_or_create_log(
            db, user_id=user_id, activity_id=activity_id, log_date=today
        )

        if activity.type == ActivityType.CHECKBOX:
            log.value_bool = not log.value_bool
            await db.commit()

        elif activity.type == ActivityType.TIME:
            user_data = await state.get_data()
            running_timers = user_data.get("running_timers", {})

            if activity.id in running_timers:
                # Останавливаем таймер
                start_time = running_timers.pop(activity.id)
                duration_seconds = time.time() - start_time
                duration_minutes = round(duration_seconds / 60)

                if log.value_minutes is None:
                    log.value_minutes = 0
                log.value_minutes += duration_minutes
                await db.commit()
            else:
                # Запускаем таймер
                running_timers[activity.id] = time.time()

            await state.update_data(running_timers=running_timers)

        # Обновляем клавиатуру, чтобы показать изменения
        await _get_and_show_activities(
            user_id=user_id, state=state, db=session, callback=callback
        )

    await callback.answer()
