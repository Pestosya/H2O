# handlers/paid.py

from aiogram import types, Router
from handlers.payment import send_invoice
from core.database import add_user, add_username

router = Router()

paid_options = {
    "paid_config_1": {"months": 1},
    "paid_config_3": {"months": 3},
    "paid_config_6": {"months": 6},
    "paid_config_12": {"months": 12},
}


@router.callback_query(lambda c: c.data in paid_options)
async def handle_paid_config_callback(callback: types.CallbackQuery):
    tg_id = callback.from_user.id
    option_key = callback.data
    months = paid_options[option_key]["months"]

    # Обновляем профиль (если нужно)
    username = callback.from_user.username or "Anon"
    await add_user(tg_id, username)
    await add_username(tg_id, username)

    # Редактируем сообщение на «🔄 Формируем счёт…»
    await callback.message.edit_text(
        f"🔄 Формируем счёт для тарифа *{months}* мес…\n\n"
        "Пожалуйста, подождите.",
        parse_mode="Markdown"
    )
    await callback.answer()

    # Сформируем payload и отправим Invoice
    payload = f"{tg_id}:{option_key}"
    invoice_message = await send_invoice(callback, payload)

    # Если инвойс пришёл успешно, удаляем «заглушку»
    if invoice_message:
        await callback.message.delete()
