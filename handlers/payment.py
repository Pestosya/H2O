# handlers/payment.py

import logging
from datetime import datetime, timedelta

from aiogram import types
from aiogram.types import (
    LabeledPrice,
    PreCheckoutQuery,
    SuccessfulPayment,
    Message,
    BufferedInputFile,
)
from aiogram import Router

from config import PAYMENT_PROVIDER_TOKEN
from session import api_session
from keyboards.menu import get_main_menu, get_config_menu, back_menu
from core.database import (
    save_config_id,
    set_expiration_time,
    enable_config,
    get_user,
)

logger = logging.getLogger(__name__)
router = Router()

# Здесь — цена и длительность по ключу
paid_options = {
    "paid_config_1": {"price_rub": 250, "hours": 730},
    "paid_config_3": {"price_rub": 690, "hours": 2190},
    "paid_config_6": {"price_rub": 1300, "hours": 4380},
    "paid_config_12": {"price_rub": 2400, "hours": 8761},
}


async def send_invoice(callback: types.CallbackQuery, payload: str):
    """
    1. Разбираем payload = "<tg_id>:<option_key>"
    2. Формируем Invoice и вызываем answer_invoice (новое сообщение).
    """
    # Разбираем payload
    try:
        tg_id_str, option_key = payload.split(":")
        tg_id = int(tg_id_str)
    except Exception:
        # Если payload сломан, возвращаем alert
        await callback.answer("❌ Ошибка данных платежа. Попробуйте ещё раз.", show_alert=True)
        return

    # Проверяем, что такой тариф есть
    if option_key not in paid_options:
        await callback.answer("❌ Неизвестный тариф.", show_alert=True)
        return

    params = paid_options[option_key]
    price_rub = params["price_rub"]
    hours = params["hours"]
    months = int(option_key.split("_")[-1])

    title = f"VPN: подписка на {months} мес."
    description = f"Платный конфиг: {months} мес. ({hours} ч.), {price_rub} ₽"
    amount = price_rub * 100  # сумма в копейках
    prices = [LabeledPrice(label=title, amount=amount)]

    # Отправляем Invoice (это новое сообщение, Telegram не поддерживает edit_text для Invoice)
    try:
        await callback.message.answer_invoice(
            title=title,
            description=description,
            payload=payload,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="vpn_payment"
        )
    except Exception as e:
        logger.error(f"Не удалось отправить Invoice: {e}")
        await callback.answer("❌ Не удалось сформировать счёт. Попробуйте позже.", show_alert=True)
        return

    # Снимаем «часики» в случае, если чей-то callback ещё открыт
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_q: PreCheckoutQuery):
    """
    Всегда отвечаем ok=True, чтобы разрешить оплату в Telegram.
    """
    await pre_checkout_q.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def handle_successful_payment(message: Message):
    """
    1) Telegram подтвердил оплату (SuccessfulPayment).
    2) Разбираем payload, создаём конфиг, сохраняем в БД.
    3) Отправляем файл .conf (новое сообщение).
    4) Редактируем сообщение-заменитель (которое «🔄 Формируем счёт…»)
       на «✅ Ваш платный конфиг активен до …» + главное меню.
    """
    payment: SuccessfulPayment = message.successful_payment
    payload = payment.invoice_payload  # "<tg_id>:<option_key>"

    try:
        tg_id_str, option_key = payload.split(":")
        tg_id = int(tg_id_str)
    except Exception as e:
        logger.error(f"Неверный payload: {payload} ({e})")
        # Здесь используем обычное сообщение, т.к. нет callback, поэтому alert недоступен
        await message.answer("❌ Ошибка данных платежа. Обратитесь в поддержку.")
        return

    if message.from_user.id != tg_id:
        await message.answer("❌ Данные платежа не соответствуют вашему Telegram ID.")
        return

    if option_key not in paid_options:
        await message.answer("❌ Неизвестный тариф.")
        return

    params = paid_options[option_key]
    hours = params["hours"]

    try:
        # 1) Создаём клиента через внешний API WireGuard
        create_resp = api_session.request(
            method="POST",
            endpoint="wireguard/client/",
            json={"name": f"{tg_id}_{option_key}"}
        )
        if create_resp.status_code != 200:
            logger.error(f"API create error (paid): {create_resp.text}")
            await message.answer("❌ Не удалось создать платный конфиг. Попробуйте позже.")
            return

        # 2) Получаем список клиентов и ищем наш
        list_resp = api_session.request(method="GET", endpoint="wireguard/client/")
        if list_resp.status_code != 200:
            logger.error(f"API list error (paid): {list_resp.text}")
            await message.answer("❌ Ошибка при получении списка конфигураций.")
            return

        configs = list_resp.json()
        config_entry = next(
            (c for c in configs if c["name"] == f"{tg_id}_{option_key}"), None
        )
        if not config_entry:
            await message.answer("❌ Конфигурация не найдена.")
            return

        paid_config_id = config_entry["id"]

        # 3) Сохраняем config_id в БД
        await save_config_id(tg_id, paid_config_id)

        # 4) Запрашиваем и отправляем файл .conf (новое сообщение)
        file_resp = api_session.request(
            method="GET",
            endpoint=f"wireguard/client/{paid_config_id}/configuration"
        )
        if file_resp.status_code != 200:
            logger.error(f"API config file error (paid): {file_resp.text}")
            await message.answer("❌ Не удалось получить файл конфигурации.")
            return

        config_file = BufferedInputFile(
            file=file_resp.content,
            filename=f"{tg_id}_paid.conf"
        )
        await message.answer_document(config_file)

        # 5) Отметим в БД expiry и активируем
        expiration = datetime.utcnow() + timedelta(hours=hours)
        await set_expiration_time(tg_id, expiration)
        await enable_config(tg_id)

        # 6) Редактируем то же сообщение-заменитель («🔄 Формируем счёт…»),
        #    выводим итог и главное меню:
        new_text = (
            f"✅ Ваш платный конфиг активен до *{expiration.strftime('%Y-%m-%d %H:%M:%S')}* UTC.\n\n"
            "Выберите следующее действие:"
        )
        await message.edit_text(new_text, parse_mode="Markdown", reply_markup=get_main_menu())

    except Exception as e:
        logger.error(f"Ошибка в handle_successful_payment: {e}")
        await message.answer("⚠️ Внутренняя ошибка при обработке платежа.")


@router.callback_query(lambda c: c.data == "back_to_config_menu")
async def handle_back_to_config(callback: types.CallbackQuery):
    """
    Возврат из раздела оплаты (если нужно) обратно
    в меню выбора тарифов (edit_text).
    """
    tg_id = callback.from_user.id
    user = await get_user(tg_id)

    if not user:
        await callback.answer("Сначала /start.", show_alert=True)
        return

    text = "🔧 *Меню конфигураций:*\n\nВыберите тип конфига:"
    keyboard = get_config_menu()
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()
