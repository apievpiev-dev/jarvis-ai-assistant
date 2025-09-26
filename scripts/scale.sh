#!/bin/bash

# Скрипт масштабирования Jarvis AI Assistant
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
LOG_FILE="/workspace/jarvis/logs/scale.log"

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Масштабирование Docker Compose сервисов
scale_docker_compose() {
    local service="$1"
    local replicas="$2"
    
    log_info "Масштабирование Docker Compose сервиса: $service до $replicas реплик..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d --scale "$service=$replicas"
        log_success "Docker Compose сервис $service масштабирован до $replicas реплик"
        log_to_file "SUCCESS: Docker Compose сервис $service масштабирован до $replicas реплик"
    else
        log_error "docker-compose.yml не найден"
        log_to_file "ERROR: docker-compose.yml не найден"
        exit 1
    fi
}

# Масштабирование Kubernetes сервисов
scale_kubernetes() {
    local deployment="$1"
    local replicas="$2"
    
    log_info "Масштабирование Kubernetes deployment: $deployment до $replicas реплик..."
    
    if kubectl get deployment "$deployment" -n jarvis &> /dev/null; then
        kubectl scale deployment "$deployment" --replicas="$replicas" -n jarvis
        log_success "Kubernetes deployment $deployment масштабирован до $replicas реплик"
        log_to_file "SUCCESS: Kubernetes deployment $deployment масштабирован до $replicas реплик"
    else
        log_error "Kubernetes deployment $deployment не найден"
        log_to_file "ERROR: Kubernetes deployment $deployment не найден"
        exit 1
    fi
}

# Проверка статуса масштабирования
check_scaling_status() {
    local service="$1"
    local replicas="$2"
    
    log_info "Проверка статуса масштабирования..."
    
    # Проверка Docker Compose
    if [ -f "docker-compose.yml" ]; then
        log_info "Статус Docker Compose сервисов:"
        docker-compose ps
    fi
    
    # Проверка Kubernetes
    if kubectl get namespace jarvis &> /dev/null; then
        log_info "Статус Kubernetes подов:"
        kubectl get pods -n jarvis
    fi
    
    log_success "Проверка статуса масштабирования завершена"
    log_to_file "SUCCESS: Проверка статуса масштабирования завершена"
}

# Автоматическое масштабирование на основе нагрузки
auto_scale() {
    local service="$1"
    local min_replicas="${2:-1}"
    local max_replicas="${3:-5}"
    local cpu_threshold="${4:-70}"
    
    log_info "Автоматическое масштабирование сервиса: $service"
    log_info "Минимум реплик: $min_replicas, Максимум реплик: $max_replicas"
    log_info "Порог CPU: $cpu_threshold%"
    
    # Получение текущего использования CPU
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    
    # Получение текущего количества реплик
    local current_replicas=$(docker-compose ps -q "$service" | wc -l)
    
    log_info "Текущее использование CPU: ${cpu_usage}%"
    log_info "Текущее количество реплик: $current_replicas"
    
    # Определение нового количества реплик
    local new_replicas=$current_replicas
    
    if (( $(echo "$cpu_usage > $cpu_threshold" | bc -l) )); then
        # Увеличение количества реплик
        new_replicas=$((current_replicas + 1))
        if [ "$new_replicas" -gt "$max_replicas" ]; then
            new_replicas=$max_replicas
        fi
        log_info "Увеличение количества реплик до $new_replicas"
    elif (( $(echo "$cpu_usage < $((cpu_threshold / 2))" | bc -l) )); then
        # Уменьшение количества реплик
        new_replicas=$((current_replicas - 1))
        if [ "$new_replicas" -lt "$min_replicas" ]; then
            new_replicas=$min_replicas
        fi
        log_info "Уменьшение количества реплик до $new_replicas"
    fi
    
    # Применение масштабирования
    if [ "$new_replicas" -ne "$current_replicas" ]; then
        scale_docker_compose "$service" "$new_replicas"
        log_success "Автоматическое масштабирование применено: $current_replicas -> $new_replicas"
        log_to_file "SUCCESS: Автоматическое масштабирование применено: $current_replicas -> $new_replicas"
    else
        log_info "Масштабирование не требуется"
        log_to_file "INFO: Масштабирование не требуется"
    fi
}

# Просмотр справки
show_help() {
    echo "Использование: $0 [опции] <сервис> <количество_реплик>"
    echo
    echo "Опции:"
    echo "  -h, --help              Показать эту справку"
    echo "  -k, --kubernetes        Масштабирование в Kubernetes"
    echo "  -a, --auto              Автоматическое масштабирование"
    echo "  -m, --min <число>       Минимальное количество реплик (для авто-масштабирования)"
    echo "  -x, --max <число>       Максимальное количество реплик (для авто-масштабирования)"
    echo "  -c, --cpu <процент>     Порог CPU для авто-масштабирования (по умолчанию: 70)"
    echo
    echo "Сервисы:"
    echo "  api-gateway             API Gateway"
    echo "  voice-service           Voice Service"
    echo "  brain-service           Brain Service"
    echo "  task-service            Task Service"
    echo "  web-service             Web Service"
    echo "  code-service            Code Service"
    echo "  learning-service        Learning Service"
    echo
    echo "Примеры:"
    echo "  $0 api-gateway 3        Масштабирование API Gateway до 3 реплик"
    echo "  $0 -k api-gateway 5     Масштабирование в Kubernetes до 5 реплик"
    echo "  $0 -a api-gateway       Автоматическое масштабирование API Gateway"
    echo "  $0 -a web-service -m 2 -x 10 -c 80  Авто-масштабирование с настройками"
}

# Основная функция
main() {
    local kubernetes_flag=false
    local auto_scale_flag=false
    local min_replicas=1
    local max_replicas=5
    local cpu_threshold=70
    local service=""
    local replicas=""
    
    # Парсинг аргументов
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -k|--kubernetes)
                kubernetes_flag=true
                shift
                ;;
            -a|--auto)
                auto_scale_flag=true
                shift
                ;;
            -m|--min)
                min_replicas="$2"
                shift 2
                ;;
            -x|--max)
                max_replicas="$2"
                shift 2
                ;;
            -c|--cpu)
                cpu_threshold="$2"
                shift 2
                ;;
            *)
                if [ -z "$service" ]; then
                    service="$1"
                elif [ -z "$replicas" ]; then
                    replicas="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Проверка аргументов
    if [ -z "$service" ]; then
        log_error "Не указан сервис для масштабирования"
        show_help
        exit 1
    fi
    
    if [ "$auto_scale_flag" = false ] && [ -z "$replicas" ]; then
        log_error "Не указано количество реплик"
        show_help
        exit 1
    fi
    
    echo "=========================================="
    echo "  Jarvis AI Assistant - Scale Script"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Начало масштабирования сервиса: $service"
    
    if [ "$auto_scale_flag" = true ]; then
        auto_scale "$service" "$min_replicas" "$max_replicas" "$cpu_threshold"
    elif [ "$kubernetes_flag" = true ]; then
        scale_kubernetes "$service" "$replicas"
    else
        scale_docker_compose "$service" "$replicas"
    fi
    
    check_scaling_status "$service" "$replicas"
    
    log_to_file "SUCCESS: Масштабирование сервиса $service завершено"
    
    echo
    echo "=========================================="
    echo "  Масштабирование завершено!"
    echo "=========================================="
    echo
    echo "Сервис: $service"
    echo "Реплики: $replicas"
    echo
    echo "Проверка статуса:"
    echo "  docker-compose ps"
    echo "  kubectl get pods -n jarvis"
    echo
    echo "Лог масштабирования: $LOG_FILE"
    echo
}

# Запуск основной функции
main "$@"