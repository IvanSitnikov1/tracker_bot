"""Общие обработчики команд (start, menu)."""

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from src.bot.keyboards.reply import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message):
    """Обработчик команды /start."""
    keyboard = get_main_menu_keyboard()
    await message.answer(
        "Привет! Я бот для трекинга активностей. "
        "Используй меню ниже для навигации.",
        reply_markup=keyboard,
    )


@router.message(Command("menu"))
async def handle_menu(message: Message):
    """Обработчик команды /menu."""
    keyboard = get_main_menu_keyboard()
    await message.answer("Главное меню:", reply_markup=keyboard)
