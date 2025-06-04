# handlers/back.py

from aiogram import types, Router
from core.database import get_user
from keyboards.menu import get_main_menu

router = Router()


@router.callback_query(lambda c: c.data == "back")
async def handle_back(callback: types.CallbackQuery):
    """
    Обработка нажатия «↩️ Назад» в разделе «Мой профиль»:
    1) Достаём из БД данные о пользователе (username и статус конфигурации).
    2) Формируем текст в точности как при /start (привет + статус).
    3) Редактируем текущее сообщение, заменяя его на главный экран с меню.
    """
    tg_id = callback.from_user.id

    # 1) Получаем данные пользователя из БД
    user_data = await get_user(tg_id)
    if not user_data:
        # Если вдруг его нет — просто отвечаем и ничего не делаем
        await callback.answer()
        return

    username = user_data.get("username") or "—"
    status = user_data.get("config_status")
    status_text = (
        "Есть активная конфигурация"
        if status == "active"
        else "Без конфигурации"
    )

    # 2) Формируем текст механизма /start
    text = (
        f"Привет, {username}!\n"
        f"Ваш статус: {status_text}\n\n"
        "Выберите нужный пункт:"
    )

    # 3) Редактируем сообщение, заменяя на главный экран
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu()
    )
    # Убираем «часики» на кнопке
    await callback.answer()
