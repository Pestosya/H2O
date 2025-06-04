# admin/Dockerfile

FROM python:3.10-slim

# Рабочая директория спрашивает /app (корень скопированного контекста)
WORKDIR /app

# Обновим pip
RUN pip install --upgrade pip

# Устанавливаем зависимости для админки
RUN pip install fastapi uvicorn[standard] "SQLAlchemy[asyncio]==2.0.15" asyncpg jinja2 python-dotenv python-multipart

# Копируем весь проект в /app
COPY . /app

# По умолчанию запускаем uvicorn из корня, указывая путь до admin/app.py
CMD ["uvicorn", "admin.app:app", "--host", "0.0.0.0", "--port", "8000"]
