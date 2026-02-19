"""Модуль с CRUD-операциями для работы с базой данных."""
import datetime
from sqlalchemy import func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.models import Activity, ActivityType, ActivityLog


async def create_activity(
    db: AsyncSession, user_id: int, name: str, type: ActivityType
) -> Activity:
    """
    Создает новую активность для пользователя.

    Args:
        db: Асинхронная сессия базы данных.
        user_id: ID пользователя Telegram.
        name: Название активности.
        type: Тип активности (CHECKBOX или TIME).

    Returns:
        Созданный объект Activity.
    """
    new_activity = Activity(user_id=user_id, name=name, type=type)
    db.add(new_activity)
    await db.commit()
    await db.refresh(new_activity)
    return new_activity


async def get_activity_by_name(
    db: AsyncSession, user_id: int, name: str
) -> Activity | None:
    """
    Получает активность пользователя по ее имени.

    Args:
        db: Асинхронная сессия базы данных.
        user_id: ID пользователя Telegram.
        name: Название активности.

    Returns:
        Объект Activity или None, если не найдено.
    """
    result = await db.execute(
        select(Activity).where(Activity.user_id == user_id, Activity.name == name)
    )
    return result.scalars().first()


async def get_user_activities(db: AsyncSession, user_id: int) -> list[Activity]:
    """
    Получает все активности пользователя.

    Args:
        db: Асинхронная сессия базы данных.
        user_id: ID пользователя Telegram.

    Returns:
        Список объектов Activity пользователя.
    """
    result = await db.execute(
        select(Activity).where(Activity.user_id == user_id).order_by(Activity.id)
    )
    return list(result.scalars().all())


async def get_activity_by_id(
    db: AsyncSession, user_id: int, activity_id: int
) -> Activity | None:
    """
    Получает активность пользователя по ее ID.
    Проверяет, что активность принадлежит пользователю.
    """
    result = await db.execute(
        select(Activity).where(
            Activity.id == activity_id, Activity.user_id == user_id
        )
    )
    return result.scalars().first()


async def get_or_create_log(
    db: AsyncSession, user_id: int, activity_id: int, log_date: datetime.date
) -> ActivityLog:
    """
    Получает или создает лог для активности на указанную дату.
    Для Checkbox инициализирует False, для Time - 0.
    """
    # Сначала убедимся, что активность принадлежит пользователю
    activity = await get_activity_by_id(db, user_id, activity_id)
    if not activity:
        raise ValueError("Activity not found or does not belong to the user")

    result = await db.execute(
        select(ActivityLog).where(
            ActivityLog.activity_id == activity_id, ActivityLog.date == log_date
        )
    )
    log = result.scalars().first()

    if not log:
        log = ActivityLog(activity_id=activity_id, date=log_date)
        if activity.type == ActivityType.CHECKBOX:
            log.value_bool = False
        elif activity.type == ActivityType.TIME:
            log.value_minutes = 0

        db.add(log)
        await db.commit()
        await db.refresh(log)

    return log


async def get_today_logs_for_user_activities(
    db: AsyncSession, user_id: int
) -> dict[int, ActivityLog]:
    """Получает все логи пользователя за сегодня в виде словаря {activity_id: log}."""
    today = datetime.date.today()
    result = await db.execute(
        select(ActivityLog)
        .join(Activity, Activity.id == ActivityLog.activity_id)
        .where(Activity.user_id == user_id, ActivityLog.date == today)
    )
    logs_list = result.scalars().all()
    return {log.activity_id: log for log in logs_list}


async def get_user_logs_for_period(
    db: AsyncSession, user_id: int, start_date: datetime.date, end_date: datetime.date
) -> list[ActivityLog]:
    """Получает все логи пользователя за указанный период."""
    result = await db.execute(
        select(ActivityLog)
        .join(Activity, Activity.id == ActivityLog.activity_id)
        .where(Activity.user_id == user_id, ActivityLog.date.between(start_date, end_date))
        .order_by(ActivityLog.date)
    )
    return list(result.scalars().all())


async def get_user_stats_for_period(
    db: AsyncSession, user_id: int, start_date: datetime.date, end_date: datetime.date
) -> list[tuple[str, ActivityType, int | None, int | None]]:
    """
    Собирает статистику по активностям пользователя за указанный период.

    Возвращает список кортежей:
    (activity_name, activity_type, total_minutes, total_checks)
    """
    query = (
        select(
            Activity.name,
            Activity.type,
            func.sum(ActivityLog.value_minutes).label("total_minutes"),
            func.sum(case((ActivityLog.value_bool, 1), else_=0)).label(
                "total_checks"
            ),
        )
        .join(ActivityLog, Activity.id == ActivityLog.activity_id)
        .where(
            Activity.user_id == user_id,
            ActivityLog.date.between(start_date, end_date),
        )
        .group_by(Activity.id, Activity.name, Activity.type)
        .order_by(Activity.id)
    )
    result = await db.execute(query)
    return result.all()
