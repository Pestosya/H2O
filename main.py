# main.py

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import PreCheckoutQuery, Message, ContentType

from config import BOT_TOKEN
from core.database import init_db, shutdown_db
from handlers.auto_disable import schedule_disable_configs

# Routers
from handlers.start import router as start_router
from handlers.get_config import router as get_config_router
from handlers.paid import router as paid_router
from handlers.payment import router as payment_router
from handlers.trial import router as trial_router
from handlers.send_config import router as send_config_router
from handlers.my_profile import router as my_profile_router
from handlers.instruction import router as instruction_router
from handlers.support import router as support_router
from handlers.back import router as back_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, dp: Dispatcher):
    await init_db()
    asyncio.create_task(schedule_disable_configs(bot))


async def on_shutdown(bot: Bot, dp: Dispatcher):
    await shutdown_db()
    await bot.session.close()


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем все роутеры из handlers/
    dp.include_router(start_router)
    dp.include_router(get_config_router)
    dp.include_router(paid_router)
    dp.include_router(payment_router)
    dp.include_router(trial_router)
    dp.include_router(send_config_router)
    dp.include_router(my_profile_router)
    dp.include_router(instruction_router)
    dp.include_router(support_router)
    dp.include_router(back_router)

    # Глобальная обработка pre_checkout_query (если не сработает в payment_router)

    await on_startup(bot, dp)
    try:
        await dp.start_polling(bot)
    finally:
        await on_shutdown(bot, dp)


if __name__ == "__main__":
    asyncio.run(main())
