# handlers/paid.py

from aiogram import types, Router

# Импортируем send_invoice из payment, чтобы там собран весь Invoice-флоу
from handlers.payment import send_invoice
from core.database import add_user, add_username

router = Router()

# Задаём только месяцы — детализацию (цена, часы и т.п.) забираем из payment.py
paid_options = {
    "paid_config_1": {"months": 1},
    "paid_config_3": {"months": 3},
    "paid_config_6": {"months": 6},
    "paid_config_12": {"months": 12},
}


@router.callback_query(lambda c: c.data in paid_options.keys())
async def handle_paid_config_callback(callback: types.CallbackQuery):
    """
    1) Пользователь нажал “paid_config_X” в меню.
    2) Мы редактируем старое сообщение на “🔄 Формируем счёт…”
    3) После edit_text сразу вызываем send_invoice(callback, payload),
       чтобы отправить реальный Invoice.
    """
    tg_id = callback.from_user.id
    option_key = callback.data  # например, "paid_config_3"
    months = paid_options[option_key]["months"]

    # 1) Создаём/обновляем профиль пользователя
    username = callback.from_user.username or "Anon"
    await add_user(tg_id, username)
    await add_username(tg_id, username)

    # 2) Редактируем текущее сообщение
    await callback.message.edit_text(
        f"🔄 Формируем счёт для тарифа *{months}* мес…\n\n"
        "Пожалуйста, подождите."
    )
    # Убираем индикатор «часиков»
    await callback.answer()

    # 3) Сформируем payload = "<tg_id>:<option_key>"
    payload = f"{tg_id}:{option_key}"

    # 4) Вызываем send_invoice из payment.py, он сделает answer_invoice()
    await send_invoice(callback, payload)
