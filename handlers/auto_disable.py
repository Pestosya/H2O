# handlers/auto_disable.py

import asyncio
from datetime import datetime

from aiogram import Bot

from session import api_session
from core.database import get_all_users, disable_config, mark_as_notified

async def disable_expired_configs(bot: Bot):
    """
    Проверяет всех пользователей и отключает «active» конфиги, у которых истёк expiration_time.
    При первом обнаружении отправляет уведомление и помечает пользователя как «notified».
    """
    now = datetime.utcnow()
    users = await get_all_users()

    for u in users:
        tg_id_str = u["telegram_id"]
        config_id = u.get("config_id")
        exp_time = u.get("expiration_time")
        status = u.get("config_status")
        notified = u.get("notified", False)

        # Пропускаем, если нет платного конфига или он не активен
        if not config_id or status != "active" or not exp_time:
            continue

        # exp_time сейчас уже datetime, но если вдруг строка — пытаемся распарсить
        if isinstance(exp_time, str):
            try:
                exp_time = datetime.fromisoformat(exp_time)
            except ValueError:
                # Некорректный формат, пропускаем
                continue

        # Если время прошло — отключаем
        if now > exp_time:
            try:
                # Отключаем конфиг через внешний API
                api_session.request(
                    method="POST",
                    endpoint=f"wireguard/client/{config_id}/disable"
                )
                # Обновляем статус в БД
                await disable_config(int(tg_id_str))

                # Если ещё не уведомляли — отправляем сообщение и помечаем «notified = True»
                if not notified:
                    await bot.send_message(
                        chat_id=int(tg_id_str),
                        text=(
                            "⚠️ Срок действия вашего платного конфига истёк, он был отключён.\n"
                            "Чтобы восстановить доступ, продлите подписку через главное меню."
                        )
                    )
                    await mark_as_notified(int(tg_id_str))

            except Exception as e:
                print(f"Ошибка при отключении конфига {config_id} для пользователя {tg_id_str}: {e}")


async def schedule_disable_configs(bot: Bot):
    """
    Фоновая задача — каждые 60 минут вызывает disable_expired_configs.
    """
    while True:
        await disable_expired_configs(bot)
        await asyncio.sleep(60)
