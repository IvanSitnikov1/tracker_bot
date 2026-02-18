"""Модуль настроек проекта."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Класс для хранения и валидации настроек проекта.

    Аттрибуты:
        bot_token (str): Токен Telegram-бота.
        db_url (str): URL для подключения к базе данных.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    db_url: str = "sqlite+aiosqlite:///./tracker.db"


settings = Settings()
