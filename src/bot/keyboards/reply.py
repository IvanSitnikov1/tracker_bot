"""Модуль с reply-клавиатурами."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру главного меню."""
    buttons = [
        [
            KeyboardButton(text="Добавить активность"),
            KeyboardButton(text="Активности"),
        ],
        [
            KeyboardButton(text="Скачать исходники"),
            KeyboardButton(text="Просмотр статистики"),
        ],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard
