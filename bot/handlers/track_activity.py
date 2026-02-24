"""Обработчики для отображения и трекинга активностей."""
import asyncio
import datetime
import time

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import inline as inline_kb
from bot.keyboards.callback_data import ActivityCallback
from bot.states.activity import TrackActivity
from db import crud
from db.database import get_async_session
from db.models import ActivityType

router = Router()


async def _get_and_show_activities(
    bot: Bot,
    user_id: int,
    state: FSMContext,
    db: AsyncSession,
    chat_id: int,
    message_id: int | None = None,
):
    """
    Вспомогательная функция для получения и отображения активностей.
    Может либо отправить новое сообщение, либо отредактировать существующее.
    """
    activities = await crud.get_user_activities(db, user_id=user_id)

    if not activities:
        await bot.send_message(
            chat_id,
            "У вас пока нет добавленных активностей. "
            "Нажмите 'Добавить активность', чтобы начать.",
        )
        return

    today_logs = await crud.get_today_logs_for_user_activities(db, user_id=user_id)
    user_data = await state.get_data()
    running_timers = user_data.get("running_timers", {})

    keyboard = await inline_kb.get_activities_keyboard(
        activities, today_logs, running_timers
    )

    if message_id:
        try:
            await bot.edit_message_reply_markup(
                chat_id=chat_id, message_id=message_id, reply_markup=keyboard
            )
        except Exception:
            pass
    else:
        await bot.send_message(
            chat_id, "Выберите активность для отметки:", reply_markup=keyboard
        )


@router.message(F.text == "Активности")
async def handle_activities_list(message: types.Message, state: FSMContext):
    """Отображает список всех активностей для трекинга."""
    if not message.from_user:
        return

    async for session in get_async_session():
        await _get_and_show_activities(
            bot=message.bot,
            user_id=message.from_user.id,
            state=state,
            db=session,
            chat_id=message.chat.id,
        )


@router.callback_query(ActivityCallback.filter(F.action == "track"))
async def handle_track_callback(
    callback: types.CallbackQuery, callback_data: ActivityCallback, state: FSMContext
):
    """Обрабатывает нажатие на кнопку 'track' (старт/стоп/чекбокс)."""
    if not callback.message:
        await callback.answer()
        return

    user_id = callback.from_user.id
    activity_id = callback_data.activity_id
    today = datetime.date.today()

    async for session in get_async_session():
        db: AsyncSession = session
        activity = await crud.get_activity_by_id(
            db, user_id=user_id, activity_id=activity_id
        )
        if not activity:
            await callback.answer("Активность не найдена!", show_alert=True)
            return

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
                start_time = running_timers.pop(activity.id)
                duration_seconds = time.time() - start_time
                duration_minutes = round(duration_seconds / 60)

                if log.value_minutes is None:
                    log.value_minutes = 0
                log.value_minutes += duration_minutes
                await db.commit()
            else:
                running_timers[activity.id] = time.time()

            await state.update_data(running_timers=running_timers)

        await _get_and_show_activities(
            bot=callback.bot,
            user_id=user_id,
            state=state,
            db=session,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
        )

    await callback.answer()


@router.callback_query(ActivityCallback.filter(F.action == "manual_time"))
async def handle_manual_time_callback(
    callback: types.CallbackQuery, callback_data: ActivityCallback, state: FSMContext
):
    """Запрашивает у пользователя время для ручного ввода."""
    if not callback.message:
        await callback.answer()
        return

    prompt_message = await callback.message.answer("Введите количество минут:")

    await state.set_state(TrackActivity.waiting_for_manual_time)
    await state.update_data(
        manual_time_activity_id=callback_data.activity_id,
        message_id_to_edit=callback.message.message_id,
        prompt_message_id=prompt_message.message_id,
    )
    await callback.answer()


@router.message(TrackActivity.waiting_for_manual_time, F.text)
async def handle_manual_time_input(message: types.Message, state: FSMContext):
    """Обрабатывает введенное вручную количество минут."""
    if not message.text or not message.text.isdigit() or not message.from_user:
        await message.answer("Пожалуйста, введите целое число.")
        return

    minutes_to_add = int(message.text)
    user_id = message.from_user.id
    user_data = await state.get_data()
    activity_id = user_data.get("manual_time_activity_id")
    message_id_to_edit = user_data.get("message_id_to_edit")
    prompt_message_id = user_data.get("prompt_message_id")

    await state.set_state(None)
    today = datetime.date.today()

    async for session in get_async_session():
        db: AsyncSession = session
        log = await crud.get_or_create_log(
            db, user_id=user_id, activity_id=activity_id, log_date=today
        )
        if log.value_minutes is None:
            log.value_minutes = 0
        log.value_minutes += minutes_to_add
        await db.commit()

        if message_id_to_edit:
            await _get_and_show_activities(
                bot=message.bot,
                user_id=user_id,
                state=state,
                db=session,
                chat_id=message.chat.id,
                message_id=message_id_to_edit,
            )

    await message.delete()
    if prompt_message_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id, message_id=prompt_message_id
            )
        except Exception:
            pass

    confirm_msg = await message.answer(f"✅ Добавлено {minutes_to_add} мин.")
    await asyncio.sleep(3)
    await confirm_msg.delete()
