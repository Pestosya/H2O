# config.py

import os
from dotenv import load_dotenv

# Загружаем .env (если есть)
load_dotenv()

# Токен вашего Telegram-бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "7810554999:AAGzNVqY-CRlPPe6Ql1CEVhe7qO5RXs2GiY")

# Базовый URL для работы с API WireGuard
API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://109.71.246.92:51821/api/wireguard/client/"
)

# Токен провайдера платежей (YooKassa)
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")

# Список админов (если используется где-то в боте)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Секрет для входа в FastAPI-админку
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "changeme")

# Строка подключения к базе данных (SQLAlchemy Async)
# Например: postgresql+asyncpg://postgres:postgres@db:5432/users_db
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/users_db"
)
