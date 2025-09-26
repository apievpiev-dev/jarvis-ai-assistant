#!/bin/bash

# Скрипт запуска Jarvis AI Assistant
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

# Конфигурация
LOG_FILE="/workspace/jarvis/logs/start.log"

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
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
    
    # Проверка .env файла
    if [ ! -f ".env" ]; then
        log_warning ".env файл не найден, создаю из примера..."
        cp .env.example .env
    fi
    
    log_success "Системные требования проверены"
    log_to_file "SUCCESS: Системные требования проверены"
}

# Сборка Docker образов
build_images() {
    log_info "Сборка Docker образов..."
    
    # Список сервисов для сборки
    services=("api-gateway" "voice-service" "brain-service" "task-service" "web-service" "code-service" "learning-service")
    
    for service in "${services[@]}"; do
        log_info "Сборка образа для $service..."
        docker build -t jarvis/$service:latest ./services/$service/
    done
    
    log_success "Docker образы собраны"
    log_to_file "SUCCESS: Docker образы собраны"
}

# Запуск сервисов
start_services() {
    log_info "Запуск сервисов..."
    
    # Запуск всех сервисов
    docker-compose up -d
    
    # Ожидание готовности сервисов
    log_info "Ожидание готовности сервисов..."
    sleep 30
    
    # Проверка статуса сервисов
    log_info "Проверка статуса сервисов..."
    docker-compose ps
    
    log_success "Сервисы запущены"
    log_to_file "SUCCESS: Сервисы запущены"
}

# Проверка работоспособности
verify_functionality() {
    log_info "Проверка работоспособности..."
    
    # Проверка доступности веб-интерфейса
    if curl -s http://localhost:3000 > /dev/null; then
        log_success "Веб-интерфейс доступен"
    else
        log_warning "Веб-интерфейс недоступен"
    fi
    
    # Проверка API Gateway
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "API Gateway доступен"
    else
        log_warning "API Gateway недоступен"
    fi
    
    # Проверка базы данных
    if docker-compose exec -T postgres pg_isready -U jarvis -d jarvis_db &> /dev/null; then
        log_success "База данных доступна"
    else
        log_warning "База данных недоступна"
    fi
    
    # Проверка Redis
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        log_success "Redis доступен"
    else
        log_warning "Redis недоступен"
    fi
    
    log_to_file "SUCCESS: Проверка работоспособности завершена"
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Start Script"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Начало запуска Jarvis AI Assistant"
    
    check_requirements
    build_images
    start_services
    verify_functionality
    
    log_to_file "SUCCESS: Jarvis AI Assistant запущен"
    
    echo
    echo "=========================================="
    echo "  Jarvis AI Assistant запущен!"
    echo "=========================================="
    echo
    echo "Веб-интерфейс: http://localhost:3000"
    echo "API Gateway: http://localhost:8000"
    echo "Grafana: http://localhost:3001"
    echo "Prometheus: http://localhost:9090"
    echo
    echo "Управление:"
    echo "  Остановка: ./scripts/stop.sh"
    echo "  Перезапуск: ./scripts/restart.sh"
    echo "  Статус: ./scripts/status.sh"
    echo "  Логи: ./scripts/logs.sh"
    echo
    echo "Проверка статуса:"
    echo "  docker-compose ps"
    echo "  docker-compose logs"
    echo
    echo "Лог запуска: $LOG_FILE"
    echo
}

# Запуск основной функции
main "$@"