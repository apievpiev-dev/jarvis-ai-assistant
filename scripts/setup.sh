#!/bin/bash

# Скрипт установки и настройки Jarvis AI Assistant
# Автор: Jarvis AI Assistant
# Версия: 1.0.0

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка системных требований
check_requirements() {
    log_info "Проверка системных требований..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен. Установите Docker и попробуйте снова."
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
        exit 1
    fi
    
    # Проверка версии Docker
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    log_info "Версия Docker: $DOCKER_VERSION"
    
    # Проверка версии Docker Compose
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    log_info "Версия Docker Compose: $COMPOSE_VERSION"
    
    # Проверка доступности портов
    check_ports() {
        local ports=(3000 8000 8001 8002 8003 8004 8005 5432 6379 9090 3001)
        for port in "${ports[@]}"; do
            if netstat -tuln 2>/dev/null | grep -q ":$port "; then
                log_warning "Порт $port уже используется"
            fi
        done
    }
    
    check_ports
    
    log_success "Системные требования проверены"
}

# Создание директорий
create_directories() {
    log_info "Создание необходимых директорий..."
    
    mkdir -p shared/models
    mkdir -p shared/memory
    mkdir -p shared/logs
    mkdir -p shared/config/grafana/dashboards
    mkdir -p shared/config/grafana/datasources
    mkdir -p shared/config/prometheus
    mkdir -p k8s
    mkdir -p scripts
    
    log_success "Директории созданы"
}

# Создание файла окружения
create_env_file() {
    log_info "Создание файла окружения..."
    
    if [ ! -f .env ]; then
        cat > .env << EOF
# Jarvis AI Assistant Environment Configuration

# Database Configuration
POSTGRES_URL=postgresql://jarvis:jarvis_password@postgres:5432/jarvis
REDIS_URL=redis://redis:6379

# Model Configuration
MODEL_PATH=./shared/models
WHISPER_MODEL=base
PHI2_MODEL=microsoft/phi-2
TTS_MODEL=tts_models/ru/ruslan
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
MODEL_DEVICE=cpu
MODEL_MAX_TOKENS=2048
MODEL_TEMPERATURE=0.7

# Service Configuration
SERVICE_NAME=jarvis
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
SERVICE_WORKERS=1
LOG_LEVEL=INFO
DEBUG=false

# Security Configuration
SECRET_KEY=jarvis-secret-key-change-in-production
JWT_EXPIRE_HOURS=24
ALLOWED_ORIGINS=*
RATE_LIMIT_PER_MINUTE=100

# Monitoring Configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=30

# Jarvis Configuration
JARVIS_LANGUAGE=ru
AUTO_LEARNING=true
VOICE_ENABLED=true
MAX_CONCURRENT_TASKS=10
TASK_TIMEOUT=300

# Web Service Configuration
REACT_APP_API_URL=http://localhost:8000
EOF
        log_success "Файл .env создан"
    else
        log_warning "Файл .env уже существует"
    fi
}

# Загрузка AI моделей
download_models() {
    log_info "Загрузка AI моделей..."
    
    # Создание скрипта загрузки моделей
    cat > scripts/download_models.py << 'EOF'
#!/usr/bin/env python3
"""
Скрипт загрузки AI моделей для Jarvis
"""
import os
import sys
import subprocess
from pathlib import Path

def download_whisper_model():
    """Загрузка модели Whisper"""
    print("Загрузка модели Whisper...")
    try:
        import whisper
        model = whisper.load_model("base")
        print("✓ Whisper модель загружена")
    except Exception as e:
        print(f"✗ Ошибка загрузки Whisper: {e}")

def download_tts_model():
    """Загрузка TTS модели"""
    print("Загрузка TTS модели...")
    try:
        from TTS.api import TTS
        tts = TTS(model_name="tts_models/ru/ruslan")
        print("✓ TTS модель загружена")
    except Exception as e:
        print(f"✗ Ошибка загрузки TTS: {e}")

def download_embedding_model():
    """Загрузка модели эмбеддингов"""
    print("Загрузка модели эмбеддингов...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        print("✓ Модель эмбеддингов загружена")
    except Exception as e:
        print(f"✗ Ошибка загрузки эмбеддингов: {e}")

if __name__ == "__main__":
    print("Загрузка AI моделей для Jarvis...")
    download_whisper_model()
    download_tts_model()
    download_embedding_model()
    print("Загрузка моделей завершена!")
EOF
    
    chmod +x scripts/download_models.py
    
    log_success "Скрипт загрузки моделей создан"
    log_info "Запустите 'python scripts/download_models.py' для загрузки моделей"
}

# Сборка Docker образов
build_images() {
    log_info "Сборка Docker образов..."
    
    # Сборка всех сервисов
    docker-compose build --parallel
    
    log_success "Docker образы собраны"
}

# Запуск сервисов
start_services() {
    log_info "Запуск сервисов..."
    
    # Запуск в фоновом режиме
    docker-compose up -d
    
    log_success "Сервисы запущены"
}

# Проверка статуса сервисов
check_services() {
    log_info "Проверка статуса сервисов..."
    
    sleep 10  # Ожидание запуска сервисов
    
    # Проверка каждого сервиса
    services=("postgres" "redis" "api-gateway" "voice-service" "brain-service" "task-service" "web-service" "code-service" "learning-service")
    
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*Up"; then
            log_success "✓ $service запущен"
        else
            log_error "✗ $service не запущен"
        fi
    done
}

# Создание скриптов управления
create_management_scripts() {
    log_info "Создание скриптов управления..."
    
    # Скрипт запуска
    cat > scripts/start.sh << 'EOF'
#!/bin/bash
echo "Запуск Jarvis AI Assistant..."
docker-compose up -d
echo "Сервисы запущены. Веб-интерфейс доступен по адресу: http://localhost:3000"
EOF
    
    # Скрипт остановки
    cat > scripts/stop.sh << 'EOF'
#!/bin/bash
echo "Остановка Jarvis AI Assistant..."
docker-compose down
echo "Сервисы остановлены"
EOF
    
    # Скрипт перезапуска
    cat > scripts/restart.sh << 'EOF'
#!/bin/bash
echo "Перезапуск Jarvis AI Assistant..."
docker-compose down
docker-compose up -d
echo "Сервисы перезапущены"
EOF
    
    # Скрипт просмотра логов
    cat > scripts/logs.sh << 'EOF'
#!/bin/bash
if [ -z "$1" ]; then
    echo "Просмотр логов всех сервисов..."
    docker-compose logs -f
else
    echo "Просмотр логов сервиса: $1"
    docker-compose logs -f "$1"
fi
EOF
    
    # Скрипт обновления
    cat > scripts/update.sh << 'EOF'
#!/bin/bash
echo "Обновление Jarvis AI Assistant..."
git pull
docker-compose down
docker-compose build --parallel
docker-compose up -d
echo "Обновление завершено"
EOF
    
    # Скрипт резервного копирования
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Создание резервной копии..."
docker-compose exec postgres pg_dump -U jarvis jarvis > "$BACKUP_DIR/database.sql"
docker cp $(docker-compose ps -q redis):/data "$BACKUP_DIR/redis_data"
cp -r shared/memory "$BACKUP_DIR/"

echo "Резервная копия создана в: $BACKUP_DIR"
EOF
    
    # Скрипт восстановления
    cat > scripts/restore.sh << 'EOF'
#!/bin/bash
if [ -z "$1" ]; then
    echo "Использование: $0 <путь_к_резервной_копии>"
    exit 1
fi

BACKUP_DIR="$1"

echo "Восстановление из резервной копии: $BACKUP_DIR"
docker-compose exec -T postgres psql -U jarvis jarvis < "$BACKUP_DIR/database.sql"
docker cp "$BACKUP_DIR/redis_data" $(docker-compose ps -q redis):/data
cp -r "$BACKUP_DIR/memory" shared/

echo "Восстановление завершено"
EOF
    
    # Делаем скрипты исполняемыми
    chmod +x scripts/*.sh
    
    log_success "Скрипты управления созданы"
}

# Создание документации
create_documentation() {
    log_info "Создание документации..."
    
    # Основная документация
    cat > docs/INSTALLATION.md << 'EOF'
# Установка Jarvis AI Assistant

## Системные требования

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM (рекомендуется 8GB)
- 10GB свободного места на диске
- Linux/macOS/Windows с WSL2

## Быстрая установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd jarvis
```

2. Запустите скрипт установки:
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

3. Откройте веб-интерфейс:
```
http://localhost:3000
```

## Ручная установка

1. Создайте файл окружения:
```bash
cp .env.example .env
```

2. Соберите Docker образы:
```bash
docker-compose build
```

3. Запустите сервисы:
```bash
docker-compose up -d
```

## Проверка установки

Проверьте статус сервисов:
```bash
docker-compose ps
```

Просмотрите логи:
```bash
docker-compose logs
```

## Устранение неполадок

### Проблемы с портами
Если порты заняты, измените их в docker-compose.yml

### Проблемы с памятью
Увеличьте лимиты памяти в Docker Desktop

### Проблемы с моделями
Загрузите модели вручную:
```bash
python scripts/download_models.py
```
EOF

    # Документация по API
    cat > docs/API.md << 'EOF'
# API Документация Jarvis AI Assistant

## Базовый URL
```
http://localhost:8000
```

## Аутентификация

### Вход в систему
```bash
POST /api/auth/login
{
  "username": "admin",
  "password": "admin123"
}
```

### Обновление токена
```bash
POST /api/auth/refresh
{
  "refresh_token": "your_refresh_token"
}
```

## Voice Service

### Распознавание речи
```bash
POST /api/voice/recognize
Content-Type: multipart/form-data
audio_file: <audio_file>
```

### Синтез речи
```bash
POST /api/voice/synthesize
{
  "text": "Привет, мир!",
  "voice": "default"
}
```

## Brain Service

### Обработка команды
```bash
POST /api/brain/process_command
{
  "text": "Создай файл test.txt",
  "user_id": "user123",
  "context": {}
}
```

### Генерация ответа
```bash
POST /api/brain/generate_response
{
  "prompt": "Объясни квантовую физику",
  "context": {}
}
```

## Task Service

### Выполнение задачи
```bash
POST /api/tasks/execute_task
{
  "type": "file_create",
  "data": {
    "file_path": "/tmp/test.txt",
    "content": "Hello World"
  }
}
```

### Планирование задачи
```bash
POST /api/tasks/schedule_task
{
  "type": "backup_create",
  "data": {
    "source_path": "/data"
  },
  "schedule_time": "2024-01-01T12:00:00Z"
}
```

## WebSocket API

### Подключение
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Отправка команды
```javascript
ws.send(JSON.stringify({
  type: 'process_command',
  text: 'Привет, Jarvis!'
}));
```

### Получение ответа
```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Ответ:', data);
};
```
EOF

    # Документация по развертыванию
    cat > docs/DEPLOYMENT.md << 'EOF'
# Развертывание Jarvis AI Assistant

## Docker Compose

### Локальное развертывание
```bash
docker-compose up -d
```

### Продакшн развертывание
```bash
# Используйте docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d
```

## Kubernetes

### Создание namespace
```bash
kubectl create namespace jarvis
```

### Применение манифестов
```bash
kubectl apply -f k8s/ -n jarvis
```

### Проверка статуса
```bash
kubectl get pods -n jarvis
```

## Мониторинг

### Prometheus
- URL: http://localhost:9090
- Метрики: /metrics

### Grafana
- URL: http://localhost:3001
- Логин: admin
- Пароль: admin

## Масштабирование

### Горизонтальное масштабирование
```bash
# Увеличить количество реплик
kubectl scale deployment voice-service --replicas=3 -n jarvis
```

### Вертикальное масштабирование
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

## Резервное копирование

### Автоматическое резервное копирование
```bash
# Добавьте в crontab
0 2 * * * /path/to/jarvis/scripts/backup.sh
```

### Восстановление
```bash
./scripts/restore.sh backups/20240101_020000
```

## Обновление

### Обновление сервисов
```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Откат изменений
```bash
git checkout <previous-commit>
docker-compose down
docker-compose build
docker-compose up -d
```
EOF

    log_success "Документация создана"
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Установка"
    echo "=========================================="
    echo
    
    check_requirements
    create_directories
    create_env_file
    download_models
    build_images
    start_services
    check_services
    create_management_scripts
    create_documentation
    
    echo
    echo "=========================================="
    echo "  Установка завершена!"
    echo "=========================================="
    echo
    echo "Веб-интерфейс: http://localhost:3000"
    echo "API Gateway: http://localhost:8000"
    echo "Grafana: http://localhost:3001"
    echo "Prometheus: http://localhost:9090"
    echo
    echo "Управление сервисами:"
    echo "  Запуск: ./scripts/start.sh"
    echo "  Остановка: ./scripts/stop.sh"
    echo "  Перезапуск: ./scripts/restart.sh"
    echo "  Логи: ./scripts/logs.sh"
    echo
    echo "Документация: docs/"
    echo
}

# Запуск основной функции
main "$@"