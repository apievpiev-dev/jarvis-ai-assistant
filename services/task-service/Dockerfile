FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    zip \
    tar \
    gzip \
    bzip2 \
    xz-utils \
    file \
    tree \
    htop \
    nano \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создание директорий
RUN mkdir -p /app/workspace /app/logs

# Копирование кода
COPY . /app/
WORKDIR /app

# Установка переменных окружения
ENV PYTHONPATH=/app
ENV WORKSPACE_PATH=/app/workspace

# Открытие порта
EXPOSE 8003

# Запуск сервиса
CMD ["python", "main.py"]