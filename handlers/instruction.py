# vpn_bot/handlers/instruction.py

from aiogram import types
from aiogram import Router
from keyboards.menu import get_main_menu

router = Router()

@router.callback_query(lambda c: c.data == "instruction")
async def handle_instruction(callback: types.CallbackQuery):
    text = (
        "📖 *Инструкция по использованию бота:*\n\n"
        "1. Нажмите «Получить конфигурацию», чтобы узнать текущий статус.\n"
        "2. Если у вас нет конфигурации, выберите в меню «Тестовый конфиг» или «Платный» (1, 3, 6, 12 мес.).\n"
        "3. После оплаты дождитесь подтверждения и скачайте конфиг через «Моя конфигурация».\n"
        "4. При возникновении проблем нажмите «Поддержка».\n"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_main_menu())
    await callback.answer()
