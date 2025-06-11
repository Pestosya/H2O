# handlers/payment.py

import json
import logging
from datetime import datetime, timedelta

from aiogram import Router, types
from aiogram.types import (
    LabeledPrice,
    PreCheckoutQuery,
    SuccessfulPayment,
    BufferedInputFile,
)

from config import PAYMENT_PROVIDER_TOKEN
from session import api_session
from keyboards.menu import get_main_menu, get_config_menu
from core.database import (
    save_config_id,
    set_expiration_time,
    enable_config,
    get_user,
)

logger = logging.getLogger(__name__)
router = Router()

# Тарифы: ключ → {"price_rub": <цена в рублях>, "hours": <количество часов>}
paid_options = {
    "paid_config_1": {"price_rub": 250, "hours": 730},
    "paid_config_3": {"price_rub": 690, "hours": 2190},
    "paid_config_6": {"price_rub": 1300, "hours": 4380},
    "paid_config_12": {"price_rub": 2400, "hours": 8761},
}


@router.callback_query(lambda c: c.data in paid_options)
async def handle_paid_config_callback(callback: types.CallbackQuery):
    """
    Пользователь нажал «paid_config_X»:
    Сразу формируем и отправляем Invoice (без «🔄 Формируем счёт…»).
    """
    tg_id = callback.from_user.id
    option_key = callback.data  # например, "paid_config_3"
    # Месяцы можно взять так:
    months = int(option_key.split("_")[-1])

    # На этом этапе мы могли бы обновить/создать запись в БД о пользователе
    # (add_user, add_username), если это необходимо.

    payload = f"{tg_id}:{option_key}"
    await send_invoice(callback, payload)


async def send_invoice(callback: types.CallbackQuery, payload: str):
    """
    1) Разбираем payload = "<tg_id>:<option_key>"
    2) Формируем Invoice с передачей чековых данных (только email)
    3) Вызываем answer_invoice (новое сообщение с кнопкой «Оплатить»)
    """
    try:
        tg_id_str, option_key = payload.split(":")
        tg_id = int(tg_id_str)
    except Exception:
        await callback.answer("❌ Ошибка данных платежа. Попробуйте ещё раз.", show_alert=True)
        return

    if option_key not in paid_options:
        await callback.answer("❌ Неизвестный тариф.", show_alert=True)
        return

    params = paid_options[option_key]
    price_rub = params["price_rub"]
    hours = params["hours"]
    months = int(option_key.split("_")[-1])

    title = f"Подписка на {months} мес."
    description = f"Платный конфиг: {months} мес. ({hours} ч.), {price_rub} ₽"
    amount = price_rub * 100
    prices = [LabeledPrice(label=title, amount=amount)]

    # Формируем provider_data (чек) с единственным полем "email"
    receipt_data = {
        "receipt": {
            "items": [
                {
                    "description": title,
                    "quantity": "1.00",
                    "amount": {"value": f"{price_rub:.2f}", "currency": "RUB"},
                    "vat_code": "1"  # 1 = 20% НДС (проверьте ваш код)
                }
            ],
            "email": "",             # Telegram запросит e-mail у пользователя
            "tax_system_code": "1"   # код вашей системы налогообложения
        }
    }
    provider_data_str = json.dumps(receipt_data, ensure_ascii=False)

    try:
        await callback.message.answer_invoice(
            title=title,
            description=description,
            payload=payload,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="vpn_payment",
            need_email=True,
            send_email_to_provider=True,
            provider_data=provider_data_str
        )
    except Exception as e:
        logger.error(f"Не удалось отправить Invoice: {e}")
        await callback.answer("❌ Не удалось сформировать счёт. Попробуйте позже.", show_alert=True)
        return

    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_q: PreCheckoutQuery):
    """
    Telegram шлёт pre_checkout_query до момента списания; отвечаем ok=True.
    """
    await pre_checkout_q.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def handle_successful_payment(message: types.Message):
    """
    1) Telegram подтвердил оплату (SuccessfulPayment).
    2) Разбираем payload, проверяем, есть ли у пользователя config_id в БД:
       • Если config_id нет → создаём нового клиента с именем str(tg_id)
                            и сохраняем config_id.
       • Если config_id уже есть → пропускаем создание, используем существующий.
    3) Скачиваем и отправляем файл .conf (один и тот же) пользователю.
    4) Продлеваем expiration_time:
       • Если старый expiration_time ещё в будущем → old + hours.
       • Иначе → now + hours.
    5) После отправки .conf кидаем новое сообщение с главным меню.
    """
    payment: SuccessfulPayment = message.successful_payment
    payload = payment.invoice_payload  # "<tg_id>:<option_key>"

    try:
        tg_id_str, option_key = payload.split(":")
        tg_id = int(tg_id_str)
    except Exception as e:
        logger.error(f"Неверный payload: {payload} ({e})")
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

    # 1) Проверяем в БД наличие config_id и expiration_time
    user = await get_user(tg_id)
    existing_config_id = None
    existing_exp_str    = None

    if user:
        existing_config_id = user.get("config_id")         # config_id или None
        existing_exp_str    = user.get("expiration_time")  # строка с datetimestamp

    try:
        # Если клиента ещё нет, создаём с именем=строка telegram_id
        if not existing_config_id:
            create_resp = api_session.request(
                method="POST",
                endpoint="wireguard/client/",
                json={"name": str(tg_id)}
            )
            if create_resp.status_code != 200:
                logger.error(f"API create error: {create_resp.text}")
                await message.answer("❌ Не удалось создать платный конфиг. Попробуйте позже.")
                return

            # Получаем список клиентов и находим только что созданного по name=str(tg_id)
            list_resp = api_session.request(method="GET", endpoint="wireguard/client/")
            if list_resp.status_code != 200:
                logger.error(f"API list error: {list_resp.text}")
                await message.answer("❌ Ошибка при получении списка конфигураций.")
                return

            configs = list_resp.json()
            config_entry = next(
                (c for c in configs if c["name"] == str(tg_id)), None
            )
            if not config_entry:
                await message.answer("❌ Конфигурация не найдена.")
                return

            paid_config_id = config_entry["id"]
            # Сохраняем в БД единственный config_id
            await save_config_id(tg_id, paid_config_id)

        else:
            # Если config_id уже есть, используем его
            paid_config_id = existing_config_id

        # 2) Скачиваем и отправляем один и тот же файл .conf
        file_resp = api_session.request(
            method="GET",
            endpoint=f"wireguard/client/{paid_config_id}/configuration"
        )
        if file_resp.status_code != 200:
            logger.error(f"API config file error: {file_resp.text}")
            await message.answer("❌ Не удалось получить файл конфигурации.")
            return

        config_file = BufferedInputFile(
            file=file_resp.content,
            filename=f"{tg_id}.conf"
        )
        await message.answer_document(config_file)

        # 3) Рассчитываем новое expiration_time
        now = datetime.utcnow()
        if existing_exp_str:
            try:
                old_exp = datetime.strptime(existing_exp_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                old_exp = None
        else:
            old_exp = None

        if old_exp and old_exp > now:
            new_exp = old_exp + timedelta(hours=hours)
        else:
            new_exp = now + timedelta(hours=hours)

        # Сохраняем время окончания в БД
        await set_expiration_time(tg_id, new_exp)

        # 4) Отмечаем конфиг как активный (если у вас есть такая логика)
        await enable_config(tg_id)

        # 5) Отправляем новое сообщение с главным меню
        await message.answer(
            f"✅ Ваш платный конфиг активен до *{new_exp.strftime('%Y-%m-%d %H:%M:%S')}* UTC.\n\n"
            "Выберите следующее действие:",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

    except Exception as e:
        logger.error(f"Ошибка в handle_successful_payment: {e}")
        await message.answer("⚠️ Внутренняя ошибка при обработке платежа.")
