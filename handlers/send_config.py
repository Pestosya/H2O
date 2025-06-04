# handlers/send_config.py

from aiogram import types
from aiogram import Router
from aiogram.types import BufferedInputFile

from session import api_session
from core.database import get_user

router = Router()


@router.callback_query(lambda c: c.data == "send_config")
async def handle_send_config(callback: types.CallbackQuery):
    """
    При нажатии «send_config» бот:
    1. Берёт config_id из БД для данного пользователя.
    2. Делает запрос к API WireGuard на получение .conf.
    3. Отправляет файл пользователю.
    """
    tg_id = callback.from_user.id
    user = await get_user(tg_id)

    # 1. Проверяем, есть ли у пользователя сохранённый config_id
    if not user or not user.get("config_id"):
        await callback.answer("❌ У вас нет активного платного конфига.",show_alert=True)
        await callback.answer()
        return

    config_id = user["config_id"]

    try:
        # 2. Запрашиваем файл конфигурации у API
        resp = api_session.request(
            method="GET",
            endpoint=f"wireguard/client/{config_id}/configuration"
        )
        if resp.status_code != 200:
            await callback.answer("❌ Ошибка при получении файла конфигурации.",show_alert=True)
            return

        # 3. Формируем BufferedInputFile и отправляем
        config_file = BufferedInputFile(
            file=resp.content,
            filename=f"{tg_id}_config.conf"
        )
        await callback.message.answer_document(config_file)

    except Exception as e:
        # В случае ошибки выводим сообщение
        await callback.answer("⚠️ Произошла ошибка при отправке конфига.",show_alert=True)
        print(f"Ошибка в handle_send_config: {e}")

    await callback.answer()
