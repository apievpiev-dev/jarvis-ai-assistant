#!/bin/bash

# Скрипт очистки Jarvis AI Assistant
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
LOG_FILE="/workspace/jarvis/logs/cleanup.log"
BACKUP_DIR="/workspace/jarvis/backups"
CLEANUP_DAYS=30

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Очистка Docker
cleanup_docker() {
    log_info "Очистка Docker..."
    
    # Удаление неиспользуемых контейнеров
    log_info "Удаление неиспользуемых контейнеров..."
    docker container prune -f
    
    # Удаление неиспользуемых образов
    log_info "Удаление неиспользуемых образов..."
    docker image prune -f
    
    # Удаление неиспользуемых сетей
    log_info "Удаление неиспользуемых сетей..."
    docker network prune -f
    
    # Удаление неиспользуемых томов
    log_info "Удаление неиспользуемых томов..."
    docker volume prune -f
    
    # Удаление неиспользуемых build кэшей
    log_info "Удаление неиспользуемых build кэшей..."
    docker builder prune -f
    
    log_success "Docker очищен"
    log_to_file "SUCCESS: Docker очищен"
}

# Очистка логов
cleanup_logs() {
    log_info "Очистка логов..."
    
    # Очистка логов Docker Compose
    if [ -f "docker-compose.yml" ]; then
        log_info "Очистка логов Docker Compose..."
        docker-compose logs --no-color > /dev/null 2>&1 || true
    fi
    
    # Очистка старых логов
    log_info "Удаление логов старше $CLEANUP_DAYS дней..."
    find /workspace/jarvis/logs -name "*.log" -mtime +$CLEANUP_DAYS -delete 2>/dev/null || true
    
    # Очистка логов системы
    if [ -d "/var/log" ]; then
        log_info "Очистка системных логов..."
        sudo journalctl --vacuum-time=${CLEANUP_DAYS}d 2>/dev/null || true
    fi
    
    log_success "Логи очищены"
    log_to_file "SUCCESS: Логи очищены"
}

# Очистка временных файлов
cleanup_temp_files() {
    log_info "Очистка временных файлов..."
    
    # Очистка временных файлов проекта
    find /workspace/jarvis -name "*.tmp" -delete 2>/dev/null || true
    find /workspace/jarvis -name "*.temp" -delete 2>/dev/null || true
    find /workspace/jarvis -name ".DS_Store" -delete 2>/dev/null || true
    find /workspace/jarvis -name "Thumbs.db" -delete 2>/dev/null || true
    
    # Очистка кэша Python
    find /workspace/jarvis -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find /workspace/jarvis -name "*.pyc" -delete 2>/dev/null || true
    find /workspace/jarvis -name "*.pyo" -delete 2>/dev/null || true
    
    # Очистка кэша Node.js
    find /workspace/jarvis -name "node_modules/.cache" -type d -exec rm -rf {} + 2>/dev/null || true
    find /workspace/jarvis -name ".npm" -type d -exec rm -rf {} + 2>/dev/null || true
    
    log_success "Временные файлы очищены"
    log_to_file "SUCCESS: Временные файлы очищены"
}

# Очистка старых бэкапов
cleanup_old_backups() {
    log_info "Очистка старых бэкапов..."
    
    if [ -d "$BACKUP_DIR" ]; then
        # Удаление бэкапов старше указанного количества дней
        find "$BACKUP_DIR" -name "jarvis_backup_*.tar.gz" -mtime +$CLEANUP_DAYS -delete 2>/dev/null || true
        
        # Подсчет оставшихся бэкапов
        backup_count=$(find "$BACKUP_DIR" -name "jarvis_backup_*.tar.gz" | wc -l)
        log_info "Осталось бэкапов: $backup_count"
    else
        log_warning "Директория бэкапов не найдена"
    fi
    
    log_success "Старые бэкапы очищены"
    log_to_file "SUCCESS: Старые бэкапы очищены"
}

# Очистка базы данных
cleanup_database() {
    log_info "Очистка базы данных..."
    
    # Проверка доступности PostgreSQL
    if docker-compose exec -T postgres pg_isready -U jarvis -d jarvis_db &> /dev/null; then
        # Очистка старых логов
        log_info "Очистка старых логов в базе данных..."
        docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c "
            DELETE FROM system_logs WHERE created_at < NOW() - INTERVAL '$CLEANUP_DAYS days';
            VACUUM ANALYZE system_logs;
        " 2>/dev/null || true
        
        # Очистка старых разговоров
        log_info "Очистка старых разговоров..."
        docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c "
            DELETE FROM conversations WHERE created_at < NOW() - INTERVAL '$CLEANUP_DAYS days';
            VACUUM ANALYZE conversations;
        " 2>/dev/null || true
        
        # Очистка старых задач
        log_info "Очистка старых задач..."
        docker-compose exec -T postgres psql -U jarvis -d jarvis_db -c "
            DELETE FROM tasks WHERE created_at < NOW() - INTERVAL '$CLEANUP_DAYS days' AND status = 'completed';
            VACUUM ANALYZE tasks;
        " 2>/dev/null || true
        
        log_success "База данных очищена"
        log_to_file "SUCCESS: База данных очищена"
    else
        log_warning "PostgreSQL недоступен, пропускаем очистку БД"
        log_to_file "WARNING: PostgreSQL недоступен"
    fi
}

# Очистка Redis
cleanup_redis() {
    log_info "Очистка Redis..."
    
    # Проверка доступности Redis
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        # Очистка истекших ключей
        log_info "Очистка истекших ключей Redis..."
        docker-compose exec -T redis redis-cli --scan --pattern "*" | while read key; do
            docker-compose exec -T redis redis-cli ttl "$key" | grep -q "^-1$" && docker-compose exec -T redis redis-cli del "$key" 2>/dev/null || true
        done
        
        # Очистка кэша
        log_info "Очистка кэша Redis..."
        docker-compose exec -T redis redis-cli flushdb 2>/dev/null || true
        
        log_success "Redis очищен"
        log_to_file "SUCCESS: Redis очищен"
    else
        log_warning "Redis недоступен, пропускаем очистку"
        log_to_file "WARNING: Redis недоступен"
    fi
}

# Очистка системы
cleanup_system() {
    log_info "Очистка системы..."
    
    # Очистка кэша пакетов
    if command -v apt &> /dev/null; then
        log_info "Очистка кэша пакетов apt..."
        sudo apt autoremove -y
        sudo apt autoclean
    fi
    
    # Очистка кэша pip
    if command -v pip &> /dev/null; then
        log_info "Очистка кэша pip..."
        pip cache purge 2>/dev/null || true
    fi
    
    # Очистка кэша npm
    if command -v npm &> /dev/null; then
        log_info "Очистка кэша npm..."
        npm cache clean --force 2>/dev/null || true
    fi
    
    log_success "Система очищена"
    log_to_file "SUCCESS: Система очищена"
}

# Проверка свободного места
check_disk_space() {
    log_info "Проверка свободного места..."
    
    # Получение информации о диске
    disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    disk_free=$(df -h / | tail -1 | awk '{print $4}')
    
    log_info "Использование диска: ${disk_usage}%"
    log_info "Свободно места: $disk_free"
    
    if [ "$disk_usage" -gt 90 ]; then
        log_warning "Критически мало свободного места!"
        log_to_file "WARNING: Критически мало свободного места: ${disk_usage}%"
    else
        log_success "Достаточно свободного места"
    fi
}

# Генерация отчета очистки
generate_cleanup_report() {
    log_info "Генерация отчета очистки..."
    
    report_file="/workspace/jarvis/logs/cleanup_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
Jarvis AI Assistant - Отчет очистки
===================================

Дата очистки: $(date)
Версия: 1.0.0

Статус очистки: ЗАВЕРШЕНО

Очищенные компоненты:
- Docker: контейнеры, образы, сети, тома, build кэши
- Логи: файлы старше $CLEANUP_DAYS дней
- Временные файлы: .tmp, .temp, __pycache__, .pyc, .pyo
- Бэкапы: файлы старше $CLEANUP_DAYS дней
- База данных: старые логи, разговоры, задачи
- Redis: истекшие ключи, кэш
- Система: кэши пакетов, pip, npm

Информация о диске:
- Использование: $(df / | tail -1 | awk '{print $5}')
- Свободно: $(df -h / | tail -1 | awk '{print $4}')

Лог очистки: $LOG_FILE

EOF
    
    log_success "Отчет очистки сохранен: $report_file"
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Cleanup Script"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Начало процесса очистки"
    
    check_disk_space
    cleanup_docker
    cleanup_logs
    cleanup_temp_files
    cleanup_old_backups
    cleanup_database
    cleanup_redis
    cleanup_system
    generate_cleanup_report
    
    log_to_file "SUCCESS: Процесс очистки завершен"
    
    echo
    echo "=========================================="
    echo "  Очистка завершена!"
    echo "=========================================="
    echo
    echo "Лог очистки: $LOG_FILE"
    echo "Отчет: /workspace/jarvis/logs/cleanup_report_$(date +%Y%m%d_%H%M%S).txt"
    echo
    echo "Информация о диске:"
    echo "  Использование: $(df / | tail -1 | awk '{print $5}')"
    echo "  Свободно: $(df -h / | tail -1 | awk '{print $4}')"
    echo
}

# Запуск основной функции
main "$@"