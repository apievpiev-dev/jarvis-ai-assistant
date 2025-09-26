#!/bin/bash

# Скрипт проверки здоровья Jarvis AI Assistant
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
HEALTH_CHECK_URL="http://localhost:8000/health"
LOG_FILE="/workspace/jarvis/logs/health_check.log"
ALERT_THRESHOLD=3
FAILURE_COUNT=0

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Проверка доступности API Gateway
check_api_gateway() {
    log_info "Проверка API Gateway..."
    
    if curl -s --max-time 10 "$HEALTH_CHECK_URL" > /dev/null; then
        log_success "API Gateway доступен"
        log_to_file "SUCCESS: API Gateway доступен"
        return 0
    else
        log_error "API Gateway недоступен"
        log_to_file "ERROR: API Gateway недоступен"
        return 1
    fi
}

# Проверка веб-интерфейса
check_web_interface() {
    log_info "Проверка веб-интерфейса..."
    
    if curl -s --max-time 10 "http://localhost:3000" > /dev/null; then
        log_success "Веб-интерфейс доступен"
        log_to_file "SUCCESS: Веб-интерфейс доступен"
        return 0
    else
        log_error "Веб-интерфейс недоступен"
        log_to_file "ERROR: Веб-интерфейс недоступен"
        return 1
    fi
}

# Проверка базы данных
check_database() {
    log_info "Проверка базы данных..."
    
    if docker-compose exec -T postgres pg_isready -U jarvis -d jarvis_db &> /dev/null; then
        log_success "База данных доступна"
        log_to_file "SUCCESS: База данных доступна"
        return 0
    else
        log_error "База данных недоступна"
        log_to_file "ERROR: База данных недоступна"
        return 1
    fi
}

# Проверка Redis
check_redis() {
    log_info "Проверка Redis..."
    
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        log_success "Redis доступен"
        log_to_file "SUCCESS: Redis доступен"
        return 0
    else
        log_error "Redis недоступен"
        log_to_file "ERROR: Redis недоступен"
        return 1
    fi
}

# Проверка Docker контейнеров
check_docker_containers() {
    log_info "Проверка Docker контейнеров..."
    
    # Получение списка контейнеров
    containers=$(docker-compose ps -q)
    
    if [ -z "$containers" ]; then
        log_error "Docker контейнеры не запущены"
        log_to_file "ERROR: Docker контейнеры не запущены"
        return 1
    fi
    
    # Проверка каждого контейнера
    all_running=true
    for container in $containers; do
        status=$(docker inspect --format='{{.State.Status}}' "$container")
        name=$(docker inspect --format='{{.Name}}' "$container" | sed 's/\///')
        
        if [ "$status" != "running" ]; then
            log_error "Контейнер $name не запущен (статус: $status)"
            log_to_file "ERROR: Контейнер $name не запущен (статус: $status)"
            all_running=false
        fi
    done
    
    if [ "$all_running" = true ]; then
        log_success "Все Docker контейнеры работают"
        log_to_file "SUCCESS: Все Docker контейнеры работают"
        return 0
    else
        return 1
    fi
}

# Проверка использования ресурсов
check_resource_usage() {
    log_info "Проверка использования ресурсов..."
    
    # Проверка CPU
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    if (( $(echo "$cpu_usage > 90" | bc -l) )); then
        log_warning "Высокое использование CPU: ${cpu_usage}%"
        log_to_file "WARNING: Высокое использование CPU: ${cpu_usage}%"
    else
        log_success "Использование CPU: ${cpu_usage}%"
    fi
    
    # Проверка памяти
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        log_warning "Высокое использование памяти: ${memory_usage}%"
        log_to_file "WARNING: Высокое использование памяти: ${memory_usage}%"
    else
        log_success "Использование памяти: ${memory_usage}%"
    fi
    
    # Проверка диска
    disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 95 ]; then
        log_warning "Критическое использование диска: ${disk_usage}%"
        log_to_file "WARNING: Критическое использование диска: ${disk_usage}%"
    else
        log_success "Использование диска: ${disk_usage}%"
    fi
}

# Проверка логов на критические ошибки
check_critical_errors() {
    log_info "Проверка логов на критические ошибки..."
    
    # Проверка логов Docker Compose
    if [ -f "docker-compose.yml" ]; then
        critical_errors=$(docker-compose logs --tail=100 2>&1 | grep -i "fatal\|critical\|panic\|out of memory" | wc -l)
        if [ "$critical_errors" -gt 0 ]; then
            log_error "Найдено $critical_errors критических ошибок"
            log_to_file "ERROR: Найдено $critical_errors критических ошибок"
            return 1
        else
            log_success "Критических ошибок не найдено"
            log_to_file "SUCCESS: Критических ошибок не найдено"
            return 0
        fi
    fi
}

# Проверка мониторинга
check_monitoring() {
    log_info "Проверка мониторинга..."
    
    # Проверка Prometheus
    if curl -s --max-time 5 "http://localhost:9090" > /dev/null; then
        log_success "Prometheus доступен"
    else
        log_warning "Prometheus недоступен"
        log_to_file "WARNING: Prometheus недоступен"
    fi
    
    # Проверка Grafana
    if curl -s --max-time 5 "http://localhost:3001" > /dev/null; then
        log_success "Grafana доступен"
    else
        log_warning "Grafana недоступен"
        log_to_file "WARNING: Grafana недоступен"
    fi
}

# Автоматическое восстановление
auto_recovery() {
    log_info "Попытка автоматического восстановления..."
    
    # Перезапуск Docker Compose
    log_info "Перезапуск Docker Compose..."
    docker-compose restart
    
    # Ожидание готовности сервисов
    log_info "Ожидание готовности сервисов..."
    sleep 30
    
    # Повторная проверка
    if check_api_gateway && check_web_interface && check_database && check_redis; then
        log_success "Автоматическое восстановление успешно"
        log_to_file "SUCCESS: Автоматическое восстановление успешно"
        return 0
    else
        log_error "Автоматическое восстановление не удалось"
        log_to_file "ERROR: Автоматическое восстановление не удалось"
        return 1
    fi
}

# Отправка уведомления
send_notification() {
    local message="$1"
    log_info "Отправка уведомления: $message"
    
    # Здесь можно добавить отправку уведомлений через:
    # - Email
    # - Telegram
    # - Slack
    # - Webhook
    
    log_to_file "NOTIFICATION: $message"
}

# Основная функция проверки здоровья
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Health Check"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Начало проверки здоровья"
    
    # Выполнение всех проверок
    check_api_gateway || ((FAILURE_COUNT++))
    check_web_interface || ((FAILURE_COUNT++))
    check_database || ((FAILURE_COUNT++))
    check_redis || ((FAILURE_COUNT++))
    check_docker_containers || ((FAILURE_COUNT++))
    check_resource_usage
    check_critical_errors || ((FAILURE_COUNT++))
    check_monitoring
    
    # Оценка общего состояния
    if [ "$FAILURE_COUNT" -eq 0 ]; then
        log_success "Все проверки пройдены успешно"
        log_to_file "SUCCESS: Все проверки пройдены успешно"
        echo
        echo "=========================================="
        echo "  Система работает нормально!"
        echo "=========================================="
    elif [ "$FAILURE_COUNT" -le "$ALERT_THRESHOLD" ]; then
        log_warning "Обнаружены проблемы, но система работает"
        log_to_file "WARNING: Обнаружены проблемы, но система работает"
        echo
        echo "=========================================="
        echo "  Система работает с предупреждениями!"
        echo "=========================================="
    else
        log_error "Критические проблемы обнаружены"
        log_to_file "ERROR: Критические проблемы обнаружены"
        
        # Попытка автоматического восстановления
        if auto_recovery; then
            log_success "Система восстановлена автоматически"
        else
            log_error "Требуется ручное вмешательство"
            send_notification "Jarvis AI Assistant требует ручного вмешательства. Количество ошибок: $FAILURE_COUNT"
        fi
        
        echo
        echo "=========================================="
        echo "  Требуется внимание!"
        echo "=========================================="
    fi
    
    echo
    echo "Количество ошибок: $FAILURE_COUNT"
    echo "Лог проверки: $LOG_FILE"
    echo
}

# Запуск основной функции
main "$@"