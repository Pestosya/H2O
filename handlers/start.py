# handlers/start.py

from aiogram import types
from aiogram.filters import Command
from aiogram import Router

from core.database import add_user, add_username, get_user  # ваши асинхронные функции из database.py
from keyboards.menu import get_main_menu

router = Router()


@router.message(Command(commands=["start"]))
async def handle_start(message: types.Message):
    """
    При вводе /start:
    1) сохраняем (или обновляем) пользователя в БД;
    2) отправляем приветственный текст + главное меню.
    """
    telegram_id = message.from_user.id
    username = message.from_user.username or "Anon"

    # 1. Добавляем пользователя, если он новый, или просто получаем существующую запись
    await add_user(telegram_id, username)
    await add_username(telegram_id, username)

    # 2. Получаем из БД актуальные данные (если потребуется в дальнейшем)
    user_data = await get_user(telegram_id)

    # 3. Формируем главное меню
    keyboard = get_main_menu()

    # 4. Подготавливаем текст приветствия (при желании можно расширить)
    text = (
        f"Привет, {username}!\n"
        f"Ваш статус: "
        f"{'Есть активная конфигурация' if user_data.get('config_status') == 'active' else 'Без конфигурации'}\n\n"
        "Выберите нужный пункт:"
    )

    # 5. Отправляем сообщение с клавиатурой
    await message.answer(text, reply_markup=keyboard)
