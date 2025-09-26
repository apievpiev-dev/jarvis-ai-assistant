#!/bin/bash

# Скрипт обновления Jarvis AI Assistant
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
UPDATE_DIR="/workspace/jarvis/update_temp"
LOG_FILE="/workspace/jarvis/logs/update.log"

# Создание директорий
mkdir -p "$BACKUP_DIR" "$UPDATE_DIR" "/workspace/jarvis/logs"

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Создание бэкапа перед обновлением
create_backup() {
    log_info "Создание бэкапа перед обновлением..."
    
    if [ -f "scripts/backup.sh" ]; then
        ./scripts/backup.sh
        log_success "Бэкап создан"
        log_to_file "SUCCESS: Бэкап создан перед обновлением"
    else
        log_warning "Скрипт бэкапа не найден, пропускаем создание бэкапа"
        log_to_file "WARNING: Скрипт бэкапа не найден"
    fi
}

# Проверка системных требований
check_requirements() {
    log_info "Проверка системных требований..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен"
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен"
        exit 1
    fi
    
    # Проверка доступности интернета
    if ! ping -c 1 google.com &> /dev/null; then
        log_error "Нет подключения к интернету"
        exit 1
    fi
    
    log_success "Системные требования проверены"
    log_to_file "SUCCESS: Системные требования проверены"
}

# Обновление системы
update_system() {
    log_info "Обновление системы..."
    
    if command -v apt &> /dev/null; then
        # Обновление пакетов
        apt update
        apt upgrade -y
        
        # Очистка кэша
        apt autoremove -y
        apt autoclean
        
        log_success "Система обновлена"
        log_to_file "SUCCESS: Система обновлена"
    else
        log_warning "Система не поддерживает apt, пропускаем обновление"
        log_to_file "WARNING: Система не поддерживает apt"
    fi
}

# Обновление Docker образов
update_docker_images() {
    log_info "Обновление Docker образов..."
    
    # Список сервисов для обновления
    services=("api-gateway" "voice-service" "brain-service" "task-service" "web-service" "code-service" "learning-service")
    
    for service in "${services[@]}"; do
        log_info "Обновление образа для $service..."
        
        # Сборка нового образа
        docker build -t jarvis/$service:latest ./services/$service/
        
        if [ $? -eq 0 ]; then
            log_success "Образ $service обновлен"
            log_to_file "SUCCESS: Образ $service обновлен"
        else
            log_error "Ошибка обновления образа $service"
            log_to_file "ERROR: Ошибка обновления образа $service"
            exit 1
        fi
    done
}

# Обновление зависимостей
update_dependencies() {
    log_info "Обновление зависимостей..."
    
    # Обновление Python зависимостей
    if [ -f "requirements.txt" ]; then
        pip install --upgrade -r requirements.txt
        log_success "Python зависимости обновлены"
        log_to_file "SUCCESS: Python зависимости обновлены"
    fi
    
    # Обновление Node.js зависимостей
    if [ -f "services/web-service/package.json" ]; then
        cd services/web-service
        npm update
        cd ../..
        log_success "Node.js зависимости обновлены"
        log_to_file "SUCCESS: Node.js зависимости обновлены"
    fi
}

# Обновление моделей ИИ
update_ai_models() {
    log_info "Обновление моделей ИИ..."
    
    if [ -f "scripts/download_models.py" ]; then
        python scripts/download_models.py --update
        log_success "Модели ИИ обновлены"
        log_to_file "SUCCESS: Модели ИИ обновлены"
    else
        log_warning "Скрипт обновления моделей не найден"
        log_to_file "WARNING: Скрипт обновления моделей не найден"
    fi
}

# Применение обновлений
apply_updates() {
    log_info "Применение обновлений..."
    
    # Остановка сервисов
    log_info "Остановка сервисов..."
    docker-compose down
    
    # Запуск сервисов с новыми образами
    log_info "Запуск сервисов с новыми образами..."
    docker-compose up -d
    
    # Ожидание готовности сервисов
    log_info "Ожидание готовности сервисов..."
    sleep 30
    
    # Проверка статуса сервисов
    log_info "Проверка статуса сервисов..."
    docker-compose ps
    
    log_success "Обновления применены"
    log_to_file "SUCCESS: Обновления применены"
}

# Проверка работоспособности
verify_functionality() {
    log_info "Проверка работоспособности после обновления..."
    
    # Проверка доступности веб-интерфейса
    if curl -s http://localhost:3000 > /dev/null; then
        log_success "Веб-интерфейс доступен"
    else
        log_error "Веб-интерфейс недоступен"
        log_to_file "ERROR: Веб-интерфейс недоступен"
    fi
    
    # Проверка API Gateway
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "API Gateway доступен"
    else
        log_error "API Gateway недоступен"
        log_to_file "ERROR: API Gateway недоступен"
    fi
    
    # Проверка базы данных
    if docker-compose exec -T postgres pg_isready -U jarvis -d jarvis_db &> /dev/null; then
        log_success "База данных доступна"
    else
        log_error "База данных недоступна"
        log_to_file "ERROR: База данных недоступна"
    fi
    
    # Проверка Redis
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        log_success "Redis доступен"
    else
        log_error "Redis недоступен"
        log_to_file "ERROR: Redis недоступен"
    fi
}

# Очистка старых образов
cleanup_old_images() {
    log_info "Очистка старых Docker образов..."
    
    # Удаление неиспользуемых образов
    docker image prune -f
    
    # Удаление неиспользуемых контейнеров
    docker container prune -f
    
    # Удаление неиспользуемых сетей
    docker network prune -f
    
    # Удаление неиспользуемых томов
    docker volume prune -f
    
    log_success "Старые образы очищены"
    log_to_file "SUCCESS: Старые образы очищены"
}

# Генерация отчета обновления
generate_update_report() {
    log_info "Генерация отчета обновления..."
    
    report_file="/workspace/jarvis/logs/update_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
Jarvis AI Assistant - Отчет обновления
======================================

Дата обновления: $(date)
Версия: 1.0.0

Статус обновления: УСПЕШНО

Обновленные компоненты:
- Система: $(uname -r)
- Docker: $(docker --version)
- Docker Compose: $(docker-compose --version)

Статус сервисов после обновления:
$(docker-compose ps)

Проверка работоспособности:
- Веб-интерфейс: $(curl -s http://localhost:3000 > /dev/null && echo "Доступен" || echo "Недоступен")
- API Gateway: $(curl -s http://localhost:8000/health > /dev/null && echo "Доступен" || echo "Недоступен")
- База данных: $(docker-compose exec -T postgres pg_isready -U jarvis -d jarvis_db &> /dev/null && echo "Доступна" || echo "Недоступна")
- Redis: $(docker-compose exec -T redis redis-cli ping &> /dev/null && echo "Доступен" || echo "Недоступен")

Лог обновления: $LOG_FILE

EOF
    
    log_success "Отчет обновления сохранен: $report_file"
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Update Script"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Начало процесса обновления"
    
    check_requirements
    create_backup
    update_system
    update_docker_images
    update_dependencies
    update_ai_models
    apply_updates
    verify_functionality
    cleanup_old_images
    generate_update_report
    
    log_to_file "SUCCESS: Процесс обновления завершен успешно"
    
    echo
    echo "=========================================="
    echo "  Обновление завершено!"
    echo "=========================================="
    echo
    echo "Веб-интерфейс: http://localhost:3000"
    echo "API Gateway: http://localhost:8000"
    echo
    echo "Лог обновления: $LOG_FILE"
    echo "Отчет: /workspace/jarvis/logs/update_report_$(date +%Y%m%d_%H%M%S).txt"
    echo
    echo "Проверка статуса:"
    echo "  docker-compose ps"
    echo "  docker-compose logs"
    echo
}

# Запуск основной функции
main "$@"