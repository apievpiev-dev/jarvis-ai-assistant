FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создание директорий
RUN mkdir -p /app/logs

# Копирование кода
COPY . /app/
WORKDIR /app

# Установка переменных окружения
ENV PYTHONPATH=/app

# Открытие порта
EXPOSE 8000

# Запуск сервиса
CMD ["python", "main.py"]