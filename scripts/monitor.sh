#!/bin/bash

# Скрипт мониторинга Jarvis AI Assistant
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
LOG_FILE="/workspace/jarvis/logs/monitor.log"
ALERT_EMAIL="admin@jarvis.local"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=80
ALERT_THRESHOLD_DISK=90

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Проверка статуса Docker контейнеров
check_docker_containers() {
    log_info "Проверка статуса Docker контейнеров..."
    
    # Получение списка контейнеров
    containers=$(docker-compose ps -q)
    
    if [ -z "$containers" ]; then
        log_error "Docker контейнеры не запущены"
        log_to_file "ERROR: Docker контейнеры не запущены"
        return 1
    fi
    
    # Проверка каждого контейнера
    for container in $containers; do
        status=$(docker inspect --format='{{.State.Status}}' "$container")
        name=$(docker inspect --format='{{.Name}}' "$container" | sed 's/\///')
        
        if [ "$status" != "running" ]; then
            log_error "Контейнер $name не запущен (статус: $status)"
            log_to_file "ERROR: Контейнер $name не запущен (статус: $status)"
        else
            log_success "Контейнер $name работает"
        fi
    done
}

# Проверка использования ресурсов
check_resource_usage() {
    log_info "Проверка использования ресурсов..."
    
    # Проверка CPU
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    if (( $(echo "$cpu_usage > $ALERT_THRESHOLD_CPU" | bc -l) )); then
        log_warning "Высокое использование CPU: ${cpu_usage}%"
        log_to_file "WARNING: Высокое использование CPU: ${cpu_usage}%"
    else
        log_success "Использование CPU: ${cpu_usage}%"
    fi
    
    # Проверка памяти
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$memory_usage > $ALERT_THRESHOLD_MEMORY" | bc -l) )); then
        log_warning "Высокое использование памяти: ${memory_usage}%"
        log_to_file "WARNING: Высокое использование памяти: ${memory_usage}%"
    else
        log_success "Использование памяти: ${memory_usage}%"
    fi
    
    # Проверка диска
    disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt "$ALERT_THRESHOLD_DISK" ]; then
        log_warning "Высокое использование диска: ${disk_usage}%"
        log_to_file "WARNING: Высокое использование диска: ${disk_usage}%"
    else
        log_success "Использование диска: ${disk_usage}%"
    fi
}

# Проверка доступности сервисов
check_service_availability() {
    log_info "Проверка доступности сервисов..."
    
    # Список сервисов для проверки
    services=(
        "http://localhost:3000:Веб-интерфейс"
        "http://localhost:8000/health:API Gateway"
        "http://localhost:9090:Prometheus"
        "http://localhost:3001:Grafana"
    )
    
    for service in "${services[@]}"; do
        url=$(echo "$service" | cut -d':' -f1-2)
        name=$(echo "$service" | cut -d':' -f3)
        
        if curl -s --max-time 5 "$url" > /dev/null; then
            log_success "$name доступен"
        else
            log_error "$name недоступен"
            log_to_file "ERROR: $name недоступен"
        fi
    done
}

# Проверка базы данных
check_database() {
    log_info "Проверка базы данных..."
    
    # Проверка подключения к PostgreSQL
    if docker-compose exec -T postgres pg_isready -U jarvis -d jarvis_db &> /dev/null; then
        log_success "PostgreSQL доступен"
        
        # Проверка размера базы данных
        db_size=$(docker-compose exec -T postgres psql -U jarvis -d jarvis_db -t -c "SELECT pg_size_pretty(pg_database_size('jarvis_db'));" | tr -d ' ')
        log_info "Размер базы данных: $db_size"
        
        # Проверка количества записей в основных таблицах
        tables=("conversations" "tasks" "learning_data" "system_logs")
        for table in "${tables[@]}"; do
            count=$(docker-compose exec -T postgres psql -U jarvis -d jarvis_db -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null | tr -d ' ' || echo "0")
            log_info "Таблица $table: $count записей"
        done
    else
        log_error "PostgreSQL недоступен"
        log_to_file "ERROR: PostgreSQL недоступен"
    fi
}

# Проверка Redis
check_redis() {
    log_info "Проверка Redis..."
    
    # Проверка подключения к Redis
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        log_success "Redis доступен"
        
        # Проверка использования памяти Redis
        redis_memory=$(docker-compose exec -T redis redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
        log_info "Использование памяти Redis: $redis_memory"
        
        # Проверка количества ключей
        key_count=$(docker-compose exec -T redis redis-cli dbsize)
        log_info "Количество ключей в Redis: $key_count"
    else
        log_error "Redis недоступен"
        log_to_file "ERROR: Redis недоступен"
    fi
}

# Проверка логов на ошибки
check_logs() {
    log_info "Проверка логов на ошибки..."
    
    # Проверка логов Docker Compose
    if [ -f "docker-compose.yml" ]; then
        error_count=$(docker-compose logs --tail=100 2>&1 | grep -i "error\|exception\|failed" | wc -l)
        if [ "$error_count" -gt 0 ]; then
            log_warning "Найдено $error_count ошибок в логах"
            log_to_file "WARNING: Найдено $error_count ошибок в логах"
        else
            log_success "Ошибок в логах не найдено"
        fi
    fi
}

# Проверка обновлений
check_updates() {
    log_info "Проверка обновлений..."
    
    # Проверка обновлений Docker образов
    docker-compose pull --quiet
    
    # Проверка обновлений системы
    if command -v apt &> /dev/null; then
        updates=$(apt list --upgradable 2>/dev/null | wc -l)
        if [ "$updates" -gt 1 ]; then
            log_info "Доступно $((updates-1)) обновлений системы"
        else
            log_success "Система обновлена"
        fi
    fi
}

# Генерация отчета
generate_report() {
    log_info "Генерация отчета мониторинга..."
    
    report_file="/workspace/jarvis/logs/monitor_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
Jarvis AI Assistant - Отчет мониторинга
========================================

Дата: $(date)
Версия: 1.0.0

Статус системы:
- CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
- Память: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')
- Диск: $(df / | tail -1 | awk '{print $5}')

Статус сервисов:
$(docker-compose ps)

Статус базы данных:
$(docker-compose exec -T postgres pg_isready -U jarvis -d jarvis_db 2>&1 || echo "Недоступна")

Статус Redis:
$(docker-compose exec -T redis redis-cli ping 2>&1 || echo "Недоступен")

Последние ошибки:
$(docker-compose logs --tail=50 2>&1 | grep -i "error\|exception\|failed" | tail -10)

EOF
    
    log_success "Отчет сохранен: $report_file"
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Monitor Script"
    echo "=========================================="
    echo
    
    check_docker_containers
    check_resource_usage
    check_service_availability
    check_database
    check_redis
    check_logs
    check_updates
    generate_report
    
    echo
    echo "=========================================="
    echo "  Мониторинг завершен!"
    echo "=========================================="
    echo
    echo "Лог мониторинга: $LOG_FILE"
    echo "Отчет: /workspace/jarvis/logs/monitor_report_$(date +%Y%m%d_%H%M%S).txt"
    echo
}

# Запуск основной функции
main "$@"