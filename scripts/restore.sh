#!/bin/bash

# Скрипт восстановления Jarvis AI Assistant
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
BACKUP_DIR="/workspace/jarvis/backups"
RESTORE_DIR="/workspace/jarvis/restore_temp"

# Проверка аргументов
if [ -z "$1" ]; then
    log_error "Использование: $0 <backup_name>"
    log_info "Доступные бэкапы:"
    ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null | awk '{print $9}' | sed 's/.*\///' | sed 's/\.tar\.gz$//' || true
    exit 1
fi

BACKUP_NAME="$1"
BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"

# Проверка существования бэкапа
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Бэкап не найден: $BACKUP_FILE"
    log_info "Доступные бэкапы:"
    ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null | awk '{print $9}' | sed 's/.*\///' | sed 's/\.tar\.gz$//' || true
    exit 1
fi

# Создание временной директории
create_temp_dir() {
    log_info "Создание временной директории..."
    rm -rf "$RESTORE_DIR"
    mkdir -p "$RESTORE_DIR"
    log_success "Временная директория создана: $RESTORE_DIR"
}

# Распаковка архива
extract_backup() {
    log_info "Распаковка архива бэкапа..."
    
    cd "$RESTORE_DIR"
    tar -xzf "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        log_success "Архив распакован"
    else
        log_error "Ошибка распаковки архива"
        exit 1
    fi
}

# Остановка сервисов
stop_services() {
    log_info "Остановка сервисов..."
    
    # Остановка Docker Compose
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
        log_success "Docker Compose сервисы остановлены"
    fi
    
    # Остановка Kubernetes (если используется)
    if kubectl get namespace jarvis &> /dev/null; then
        log_info "Остановка Kubernetes сервисов..."
        kubectl delete -f k8s/ 2>/dev/null || true
        log_success "Kubernetes сервисы остановлены"
    fi
}

# Восстановление конфигураций
restore_configs() {
    log_info "Восстановление конфигураций..."
    
    # Восстановление конфигураций
    if [ -d "$RESTORE_DIR/$BACKUP_NAME/configs" ]; then
        cp -r "$RESTORE_DIR/$BACKUP_NAME/configs"/* shared/config/ 2>/dev/null || true
        log_success "Конфигурации восстановлены"
    fi
    
    # Восстановление Docker Compose файлов
    if [ -f "$RESTORE_DIR/$BACKUP_NAME/docker-compose.yml" ]; then
        cp "$RESTORE_DIR/$BACKUP_NAME/docker-compose.yml" . 2>/dev/null || true
    fi
    
    if [ -f "$RESTORE_DIR/$BACKUP_NAME/docker-compose.prod.yml" ]; then
        cp "$RESTORE_DIR/$BACKUP_NAME/docker-compose.prod.yml" . 2>/dev/null || true
    fi
    
    # Восстановление .env файла
    if [ -f "$RESTORE_DIR/$BACKUP_NAME/.env" ]; then
        cp "$RESTORE_DIR/$BACKUP_NAME/.env" . 2>/dev/null || true
    fi
    
    log_success "Конфигурационные файлы восстановлены"
}

# Восстановление базы данных
restore_database() {
    log_info "Восстановление базы данных..."
    
    # Запуск PostgreSQL
    docker-compose up -d postgres
    
    # Ожидание готовности PostgreSQL
    log_info "Ожидание готовности PostgreSQL..."
    sleep 10
    
    # Проверка доступности PostgreSQL
    if ! docker-compose exec -T postgres pg_isready -U jarvis -d jarvis_db &> /dev/null; then
        log_error "PostgreSQL недоступен"
        exit 1
    fi
    
    # Восстановление базы данных
    if [ -f "$RESTORE_DIR/$BACKUP_NAME/database.sql" ]; then
        docker-compose exec -T postgres psql -U jarvis -d jarvis_db < "$RESTORE_DIR/$BACKUP_NAME/database.sql"
        
        if [ $? -eq 0 ]; then
            log_success "База данных восстановлена"
        else
            log_error "Ошибка восстановления базы данных"
            exit 1
        fi
    else
        log_warning "Файл базы данных не найден в бэкапе"
    fi
}

# Восстановление логов
restore_logs() {
    log_info "Восстановление логов..."
    
    if [ -d "$RESTORE_DIR/$BACKUP_NAME/logs" ]; then
        mkdir -p logs
        cp -r "$RESTORE_DIR/$BACKUP_NAME/logs"/* logs/ 2>/dev/null || true
        log_success "Логи восстановлены"
    else
        log_warning "Логи не найдены в бэкапе"
    fi
}

# Восстановление моделей ИИ
restore_models() {
    log_info "Восстановление моделей ИИ..."
    
    if [ -d "$RESTORE_DIR/$BACKUP_NAME/models" ]; then
        mkdir -p shared/models
        cp -r "$RESTORE_DIR/$BACKUP_NAME/models"/* shared/models/ 2>/dev/null || true
        log_success "Модели ИИ восстановлены"
    else
        log_warning "Модели ИИ не найдены в бэкапе"
    fi
}

# Восстановление данных обучения
restore_learning_data() {
    log_info "Восстановление данных обучения..."
    
    if [ -d "$RESTORE_DIR/$BACKUP_NAME/learning" ]; then
        mkdir -p shared/memory
        cp -r "$RESTORE_DIR/$BACKUP_NAME/learning"/* shared/memory/ 2>/dev/null || true
        log_success "Данные обучения восстановлены"
    else
        log_warning "Данные обучения не найдены в бэкапе"
    fi
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
}

# Очистка временных файлов
cleanup() {
    log_info "Очистка временных файлов..."
    rm -rf "$RESTORE_DIR"
    log_success "Временные файлы очищены"
}

# Проверка восстановления
verify_restore() {
    log_info "Проверка восстановления..."
    
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
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Restore Script"
    echo "=========================================="
    echo
    
    log_info "Восстановление из бэкапа: $BACKUP_NAME"
    
    create_temp_dir
    extract_backup
    stop_services
    restore_configs
    restore_database
    restore_logs
    restore_models
    restore_learning_data
    start_services
    verify_restore
    cleanup
    
    echo
    echo "=========================================="
    echo "  Восстановление завершено!"
    echo "=========================================="
    echo
    echo "Веб-интерфейс: http://localhost:3000"
    echo "API Gateway: http://localhost:8000"
    echo
    echo "Проверка статуса:"
    echo "  docker-compose ps"
    echo "  docker-compose logs"
    echo
}

# Запуск основной функции
main "$@"