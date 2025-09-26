#!/bin/bash

# Скрипт быстрого запуска Jarvis AI Assistant
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
LOG_FILE="/workspace/jarvis/logs/quick_start.log"

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
    
    # Проверка Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 не установлен. Установите Python3 и попробуйте снова."
        exit 1
    fi
    
    # Проверка Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js не установлен. Установите Node.js и попробуйте снова."
        exit 1
    fi
    
    log_success "Системные требования проверены"
    log_to_file "SUCCESS: Системные требования проверены"
}

# Создание .env файла
create_env_file() {
    log_info "Создание .env файла..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        log_success ".env файл создан"
        log_to_file "SUCCESS: .env файл создан"
    else
        log_info ".env файл уже существует"
    fi
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

# Настройка портов
setup_ports() {
    log_info "Настройка портов..."
    
    # Функция для запуска port-forward в фоне
    start_port_forward() {
        local service=$1
        local local_port=$2
        local service_port=$3
        
        log_info "Настройка порта $local_port -> $service:$service_port"
        docker-compose port "$service" "$service_port" > /dev/null 2>&1 || true
    }
    
    # Настройка портов для основных сервисов
    start_port_forward "web-service" 3000 3000
    start_port_forward "api-gateway" 8000 8000
    start_port_forward "grafana" 3001 3000
    start_port_forward "prometheus" 9090 9090
    
    log_success "Порты настроены"
    log_to_file "SUCCESS: Порты настроены"
}

# Создание скриптов управления
create_management_scripts() {
    log_info "Создание скриптов управления..."
    
    # Скрипт остановки
    cat > scripts/stop.sh << 'EOF'
#!/bin/bash
echo "Остановка Jarvis AI Assistant..."
docker-compose down
echo "Jarvis AI Assistant остановлен"
EOF
    
    # Скрипт перезапуска
    cat > scripts/restart.sh << 'EOF'
#!/bin/bash
echo "Перезапуск Jarvis AI Assistant..."
docker-compose restart
echo "Jarvis AI Assistant перезапущен"
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
    
    # Скрипт масштабирования
    cat > scripts/scale.sh << 'EOF'
#!/bin/bash
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Использование: $0 <service> <replicas>"
    echo "Пример: $0 api-gateway 3"
    exit 1
fi

service=$1
replicas=$2

echo "Масштабирование $service до $replicas реплик..."
docker-compose up -d --scale "$service=$replicas"
echo "Масштабирование завершено"
EOF
    
    # Делаем скрипты исполняемыми
    chmod +x scripts/*.sh
    
    log_success "Скрипты управления созданы"
    log_to_file "SUCCESS: Скрипты управления созданы"
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Quick Start"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Начало быстрого запуска"
    
    check_requirements
    create_env_file
    build_images
    start_services
    verify_functionality
    setup_ports
    create_management_scripts
    
    log_to_file "SUCCESS: Быстрый запуск завершен"
    
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
    echo "  Логи: ./scripts/logs.sh"
    echo "  Масштабирование: ./scripts/scale.sh <service> <replicas>"
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