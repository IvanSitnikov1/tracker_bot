"""Модуль для настройки подключения к базе данных."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings

# Создаем асинхронный "движок" для взаимодействия с БД.
# echo=True полезно для отладки, т.к. выводит все SQL-запросы в консоль.
async_engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=False,  # В реальном приложении лучше поставить False
)

# Создаем фабрику сессий, которая будет создавать новые сессии для каждого запроса.
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncSession:
    """
    Асинхронный генератор для получения сессии базы данных.
    Обеспечивает корректное открытие и закрытие сессии.
    """
    async with async_session_factory() as session:
        yield session
