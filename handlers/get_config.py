# handlers/get_config.py

from aiogram import types
from aiogram import Router

from core.database import get_user
from keyboards.menu import get_config_menu

router = Router()


@router.callback_query(lambda c: c.data == "get_config")
async def handle_get_config(callback: types.CallbackQuery):
    """
    При нажатии «Получить конфигурацию» показываем меню с вариантами:
    - Тестовый конфиг
    - Платный 1, 3, 6, 12 месяцев
    """
    tg_id = callback.from_user.id
    user = await get_user(tg_id)

    if not user:
        await callback.message.answer("Сначала нажмите /start.")
        await callback.answer()
        return

    text = "🔧 *Меню конфигураций:*\n\nВыберите, какой тип конфига вы хотите получить:"
    keyboard = get_config_menu()
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    await callback.answer()
