"""Обработчики для добавления новой активности."""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from bot.keyboards.inline import get_activity_type_keyboard
from bot.states.activity import AddActivity
from db import crud
from db.database import get_async_session
from db.models import ActivityType

router = Router()


@router.message(F.text == "Добавить активность")
async def handle_add_activity_start(message: types.Message):
    """Начинает процесс добавления новой активности."""
    keyboard = get_activity_type_keyboard()
    await message.answer(
        "Выберите тип новой активности:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("add_activity:"))
async def handle_activity_type_selection(
    callback: types.CallbackQuery, state: FSMContext
):
    """Обрабатывает выбор типа активности и запрашивает имя."""
    activity_type_str = callback.data.split(":")[1]
    
    await state.update_data(activity_type=activity_type_str)
    await state.set_state(AddActivity.waiting_for_name)
    
    await callback.message.edit_text(
        f"""Вы выбрали тип: <b>{activity_type_str.upper()}</b>.

Теперь введите название для новой активности."""
    )
    await callback.answer()


@router.message(AddActivity.waiting_for_name)
async def handle_new_activity_name(
    message: types.Message, state: FSMContext
):
    """Сохраняет новую активность в базу данных."""
    activity_name = message.text
    user_data = await state.get_data()
    activity_type_str = user_data["activity_type"]
    activity_type = ActivityType[activity_type_str.upper()]

    async for session in get_async_session():
        db: AsyncSession = session
        try:
            # Проверяем, существует ли активность с таким именем
            existing_activity = await crud.get_activity_by_name(db, activity_name)
            if existing_activity:
                await message.answer(
                    f"Активность с названием '<b>{activity_name}</b>' уже существует. "
                    "Попробуйте другое название."
                )
                return

            # Создаем новую активность
            await crud.create_activity(
                db=db, name=activity_name, type=activity_type
            )
            await state.clear()
            await message.answer(
                f"✅ Новая активность '<b>{activity_name}</b>' "
                f"(тип: {activity_type_str}) успешно добавлена!"
            )
        except IntegrityError:
            await state.clear()
            await message.answer(
                "Произошла ошибка при добавлении активности. "
                "Возможно, такое имя уже занято."
            )
        except Exception as e:
            await state.clear()
            await message.answer(f"Произошла непредвиденная ошибка: {e}")
            
