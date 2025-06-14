# handlers/trial.py

from aiogram import types
from aiogram import Router
from aiogram.types import BufferedInputFile
from datetime import datetime, timedelta

from session import api_session
from keyboards.menu import get_main_menu, get_config_menu
from core.database import (
    add_user,
    add_username,
    has_used_trial,
    set_trial_used,
    save_trial_config_id,
    set_trial_expiration_time,
    get_user
)

router = Router()


@router.callback_query(lambda c: c.data == "trial")
async def handle_trial_callback(callback: types.CallbackQuery):
    """
    Хэндлер для кнопки «Тестовый конфиг».
    Логика:
    1. Добавляем/обновляем username в БД.
    2. Проверяем, использовал ли пользователь пробный ранее.
       - Если да → показываем алерт и выходим.
    3. Создаём нового клиента через API.
    4. Получаем список клиентов, находим только что созданный.
    5. Сохраняем config_id в БД, запрашиваем сам файл конфига.
    6. Шлем .conf-файл пользователю.
    7. Ставим время окончания через 24 часа, помечаем пробный как использованный.
    8. Редактируем предыдущее сообщение, возвращая главное меню.
    """
    tg_id = callback.from_user.id
    username = callback.from_user.username or "Anon"

    # 1. Обновляем username и создаём запись, если новая
    await add_username(tg_id, username)
    await add_user(tg_id, username)

    # 2. Проверяем, брал ли уже пробный
    if await has_used_trial(tg_id):
        await callback.answer(
            "⚠️ Вы уже использовали тестовую конфигурацию (доступна только один раз).",
            show_alert=True
        )
        return

    try:
        # 3. Создаём пробного клиента через API
        create_resp = api_session.request(
            method="POST",
            endpoint="wireguard/client/",
            json={"name": str(tg_id)}
        )
        if create_resp.status_code != 200:
            await callback.answer(
                "❌ Ошибка при создании пробного конфига. Попробуйте позже.", show_alert=True
            )
            print("API create error:", create_resp.text)
            await callback.answer()
            return

        # 4. Получаем список клиентов, ищем нужный
        list_resp = api_session.request(method="GET", endpoint="wireguard/client/")
        if list_resp.status_code != 200:
            await callback.answer(
                "❌ Не удалось получить список конфигураций. Попробуйте позже.", show_alert=True
            )
            print("API list error:", list_resp.text)
            await callback.answer()
            return

        configs = list_resp.json()
        config_entry = next((c for c in configs if c["name"] == str(tg_id)), None)
        if not config_entry:
            await callback.answer("❌ Конфигурация не найдена.", show_alert=True)
            await callback.answer()
            return

        trial_config_id = config_entry["id"]

        # 5. Сохраняем config_id в БД
        await save_trial_config_id(tg_id, trial_config_id)

        # 6. Запрашиваем файл конфигурации и отсылаем его
        file_resp = api_session.request(
            method="GET",
            endpoint=f"wireguard/client/{trial_config_id}/configuration"
        )
        if file_resp.status_code != 200:
            await callback.answer(
                "❌ Ошибка при получении файла конфигурации.", show_alert=True
            )
            print("API config file error:", file_resp.text)
            await callback.answer()
            return

        config_file = BufferedInputFile(
            file=file_resp.content,
            filename=f"{tg_id}.conf"
        )
        await callback.message.answer_document(config_file)

        # 7. Устанавливаем время окончания и помечаем пробный как использованный
        expiration_time = datetime.utcnow() + timedelta(hours=24)
        await set_trial_expiration_time(tg_id, expiration_time)
        await set_trial_used(tg_id, used=True)

        # 8. Редактируем предыдущее сообщение: возвращаем главное меню
        await callback.message.edit_text(
            f"✅ Ваш пробный конфиг будет действовать до "
            f"{expiration_time.strftime('%Y-%m-%d %H:%M:%S')} UTC.\n\n"
            "Выберите любое действие ниже:",
            reply_markup=get_main_menu()
        )

    except Exception as e:
        await callback.answer("⚠️ Произошла внутренняя ошибка, попробуйте позже.", show_alert=True)
        print("Ошибка в handle_trial_callback:", e)

    await callback.answer()
