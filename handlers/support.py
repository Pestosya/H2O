# handlers/support.py

from aiogram import types, Router
from keyboards.menu import get_main_menu

router = Router()

@router.callback_query(lambda c: c.data == "support")
async def handle_support(callback: types.CallbackQuery):
    """
    Редактируем текущее сообщение, показывая информацию о поддержке,
    и одновременно выводим главное меню (без кнопки «Назад»).
    """
    text = (
        "💬 *Поддержка*:\n"
        "Если у вас возникли вопросы, вы можете:\n"
        "1. Написать в наш Telegram-чат поддержки: [t.me/your_support_chat](https://t.me/your_support_chat)\n"
        "2. Написать на почту: support@example.com\n"
    )

    # Вместо отдельной кнопки «Назад» сразу показываем главное меню
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=get_main_menu()
    )
    await callback.answer()
