FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    festival \
    festvox-ru \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создание директорий
RUN mkdir -p /app/models /app/cache /app/logs

# Копирование кода
COPY . /app/
WORKDIR /app

# Установка переменных окружения
ENV PYTHONPATH=/app
ENV MODEL_PATH=/app/models
ENV CACHE_PATH=/app/cache

# Открытие порта
EXPOSE 8001

# Запуск сервиса
CMD ["python", "main.py"]