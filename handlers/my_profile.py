# handlers/my_profile.py

from aiogram import types
from aiogram import Router
from keyboards.menu import get_profile_menu
from core.database import get_user

router = Router()


@router.callback_query(lambda c: c.data == "my_profile")
async def handle_my_profile(callback: types.CallbackQuery):
    tg_id = callback.from_user.id
    user = await get_user(tg_id)

    if not user:
        await callback.message.answer("Сначала нажмите /start.")
    else:
        username = user.get("username") or "—"
        trial_used = "Да" if user.get("trial_used") else "Нет"
        trial_exp = user.get("trial_expiration_time") or "—"
        status = user.get("config_status") or "—"
        exp = user.get("expiration_time") or "—"
        text = (
            f"👤 *Ваш профиль:*\n\n"
            f"Username: `{username}`\n"
            f"Пробный использован: `{trial_used}` (истекает `{trial_exp}`)\n"
            f"Платный статус: `{status}` (истекает `{exp}`)\n"
        )
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_profile_menu())

    await callback.answer()
