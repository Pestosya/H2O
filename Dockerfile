# Используем официальный образ Python 3.12
FROM python:3.12-slim

# Задаём рабочую директорию внутри контейнера
WORKDIR /app

# Копируем весь проект в контейнер
COPY . /app

# Обновляем pip и устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# По умолчанию запускаем main.py
CMD ["python", "main.py"]
