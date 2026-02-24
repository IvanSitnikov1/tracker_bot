"""Главный файл приложения."""

import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI

from bot.handlers import stats as stats_handlers, download as download_handlers, \
    track_activity as track_activity_handlers, common as common_handlers, \
    add_activity as add_activity_handlers, help as help_handlers
from core.config import settings


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
storage = MemoryStorage()
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(storage=storage)

# Регистрация роутеров
dp.include_router(common_handlers.router)
dp.include_router(add_activity_handlers.router)
dp.include_router(track_activity_handlers.router)
dp.include_router(download_handlers.router)
dp.include_router(stats_handlers.router)
dp.include_router(help_handlers.router)

# Создание экземпляра FastAPI
app = FastAPI()

# URL для вебхука, должен быть защищен (https) и доступен извне
WEBHOOK_PATH = f"/bot/{settings.BOT_TOKEN}"
WEBHOOK_URL = settings.SERVER_URL + WEBHOOK_PATH


@app.on_event("startup")
async def on_startup():
    """Действия при старте приложения."""
    logger.info("Приложение запускается...")
    # Установка вебхука
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"Вебхук установлен на URL: {WEBHOOK_URL}")
    else:
        logger.info("Вебхук уже настроен.")


@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    """
    Принимает обновления от Telegram и передает их в диспетчер.
    """
    telegram_update = types.Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)


@app.on_event("shutdown")
async def on_shutdown():
    """Действия при остановке приложения."""
    logger.info("Приложение останавливается...")
    # Корректное закрытие сессии бота
    await bot.session.close()
    logger.info("Сессия бота закрыта.")


if __name__ == "__main__":
    # Этот блок для локального запуска без FastAPI (например, для отладки)
    # В продакшене будет использоваться uvicorn для запуска FastAPI.
    async def main():
        logger.info("Бот запускается в режиме опроса...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    asyncio.run(main())
