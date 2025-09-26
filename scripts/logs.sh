#!/bin/bash

# Скрипт просмотра логов Jarvis AI Assistant
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
LOG_FILE="/workspace/jarvis/logs/logs_viewer.log"

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Просмотр логов Docker Compose
view_docker_compose_logs() {
    local service="$1"
    local lines="${2:-100}"
    
    log_info "Просмотр логов Docker Compose..."
    
    if [ -z "$service" ]; then
        log_info "Просмотр логов всех сервисов..."
        docker-compose logs --tail="$lines" -f
    else
        log_info "Просмотр логов сервиса: $service"
        docker-compose logs --tail="$lines" -f "$service"
    fi
    
    log_to_file "INFO: Просмотр логов Docker Compose: $service"
}

# Просмотр логов файлов
view_file_logs() {
    local log_type="$1"
    local lines="${2:-100}"
    
    log_info "Просмотр логов файлов..."
    
    case "$log_type" in
        "install")
            if [ -f "/workspace/jarvis/logs/install_dependencies.log" ]; then
                tail -n "$lines" /workspace/jarvis/logs/install_dependencies.log
            else
                log_warning "Лог установки не найден"
            fi
            ;;
        "setup")
            if [ -f "/workspace/jarvis/logs/setup.log" ]; then
                tail -n "$lines" /workspace/jarvis/logs/setup.log
            else
                log_warning "Лог настройки не найден"
            fi
            ;;
        "start")
            if [ -f "/workspace/jarvis/logs/start.log" ]; then
                tail -n "$lines" /workspace/jarvis/logs/start.log
            else
                log_warning "Лог запуска не найден"
            fi
            ;;
        "status")
            if [ -f "/workspace/jarvis/logs/status.log" ]; then
                tail -n "$lines" /workspace/jarvis/logs/status.log
            else
                log_warning "Лог статуса не найден"
            fi
            ;;
        "health")
            if [ -f "/workspace/jarvis/logs/health_check.log" ]; then
                tail -n "$lines" /workspace/jarvis/logs/health_check.log
            else
                log_warning "Лог проверки здоровья не найден"
            fi
            ;;
        "monitor")
            if [ -f "/workspace/jarvis/logs/monitor.log" ]; then
                tail -n "$lines" /workspace/jarvis/logs/monitor.log
            else
                log_warning "Лог мониторинга не найден"
            fi
            ;;
        "backup")
            if [ -f "/workspace/jarvis/logs/backup.log" ]; then
                tail -n "$lines" /workspace/jarvis/logs/backup.log
            else
                log_warning "Лог бэкапа не найден"
            fi
            ;;
        "restore")
            if [ -f "/workspace/jarvis/logs/restore.log" ]; then
                tail -n "$lines" /workspace/jarvis/logs/restore.log
            else
                log_warning "Лог восстановления не найден"
            fi
            ;;
        "update")
            if [ -f "/workspace/jarvis/logs/update.log" ]; then
                tail -n "$lines" /workspace/jarvis/logs/update.log
            else
                log_warning "Лог обновления не найден"
            fi
            ;;
        "cleanup")
            if [ -f "/workspace/jarvis/logs/cleanup.log" ]; then
                tail -n "$lines" /workspace/jarvis/logs/cleanup.log
            else
                log_warning "Лог очистки не найден"
            fi
            ;;
        "telegram")
            if [ -f "/workspace/jarvis/logs/telegram_bot.log" ]; then
                tail -n "$lines" /workspace/jarvis/logs/telegram_bot.log
            else
                log_warning "Лог Telegram бота не найден"
            fi
            ;;
        *)
            log_error "Неизвестный тип лога: $log_type"
            log_info "Доступные типы: install, setup, start, status, health, monitor, backup, restore, update, cleanup, telegram"
            return 1
            ;;
    esac
    
    log_to_file "INFO: Просмотр логов файлов: $log_type"
}

# Просмотр системных логов
view_system_logs() {
    local lines="${1:-100}"
    
    log_info "Просмотр системных логов..."
    
    # Просмотр логов systemd
    if command -v journalctl &> /dev/null; then
        log_info "Логи systemd:"
        journalctl --no-pager -n "$lines"
    fi
    
    # Просмотр логов Docker
    if command -v docker &> /dev/null; then
        log_info "Логи Docker:"
        docker system events --since 1h --until now
    fi
    
    log_to_file "INFO: Просмотр системных логов"
}

# Поиск ошибок в логах
search_errors() {
    local service="$1"
    local lines="${2:-1000}"
    
    log_info "Поиск ошибок в логах..."
    
    if [ -z "$service" ]; then
        log_info "Поиск ошибок во всех сервисах..."
        docker-compose logs --tail="$lines" 2>&1 | grep -i "error\|exception\|failed\|critical\|fatal" || log_info "Ошибок не найдено"
    else
        log_info "Поиск ошибок в сервисе: $service"
        docker-compose logs --tail="$lines" "$service" 2>&1 | grep -i "error\|exception\|failed\|critical\|fatal" || log_info "Ошибок не найдено"
    fi
    
    log_to_file "INFO: Поиск ошибок в логах: $service"
}

# Просмотр метрик
view_metrics() {
    log_info "Просмотр метрик..."
    
    # Проверка доступности Prometheus
    if curl -s http://localhost:9090 > /dev/null; then
        log_info "Prometheus доступен: http://localhost:9090"
    else
        log_warning "Prometheus недоступен"
    fi
    
    # Проверка доступности Grafana
    if curl -s http://localhost:3001 > /dev/null; then
        log_info "Grafana доступен: http://localhost:3001"
    else
        log_warning "Grafana недоступен"
    fi
    
    # Просмотр метрик Docker
    if command -v docker &> /dev/null; then
        log_info "Метрики Docker:"
        docker stats --no-stream
    fi
    
    log_to_file "INFO: Просмотр метрик"
}

# Просмотр справки
show_help() {
    echo "Использование: $0 [опции] [сервис] [количество_строк]"
    echo
    echo "Опции:"
    echo "  -h, --help              Показать эту справку"
    echo "  -f, --follow            Следить за логами в реальном времени"
    echo "  -e, --errors            Поиск ошибок в логах"
    echo "  -m, --metrics           Просмотр метрик"
    echo "  -s, --system            Просмотр системных логов"
    echo "  -t, --type <тип>        Просмотр логов определенного типа"
    echo
    echo "Типы логов:"
    echo "  install                 Лог установки зависимостей"
    echo "  setup                   Лог настройки системы"
    echo "  start                   Лог запуска"
    echo "  status                  Лог проверки статуса"
    echo "  health                  Лог проверки здоровья"
    echo "  monitor                 Лог мониторинга"
    echo "  backup                  Лог создания бэкапов"
    echo "  restore                 Лог восстановления"
    echo "  update                  Лог обновлений"
    echo "  cleanup                 Лог очистки"
    echo "  telegram                Лог Telegram бота"
    echo
    echo "Примеры:"
    echo "  $0                      Просмотр логов всех сервисов"
    echo "  $0 api-gateway          Просмотр логов API Gateway"
    echo "  $0 -f web-service       Следить за логами Web Service"
    echo "  $0 -e                   Поиск ошибок во всех сервисах"
    echo "  $0 -t start             Просмотр лога запуска"
    echo "  $0 -m                   Просмотр метрик"
    echo "  $0 -s                   Просмотр системных логов"
}

# Основная функция
main() {
    local follow=false
    local search_errors_flag=false
    local metrics_flag=false
    local system_flag=false
    local log_type=""
    local service=""
    local lines=100
    
    # Парсинг аргументов
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -f|--follow)
                follow=true
                shift
                ;;
            -e|--errors)
                search_errors_flag=true
                shift
                ;;
            -m|--metrics)
                metrics_flag=true
                shift
                ;;
            -s|--system)
                system_flag=true
                shift
                ;;
            -t|--type)
                log_type="$2"
                shift 2
                ;;
            *)
                if [ -z "$service" ]; then
                    service="$1"
                elif [ -z "$lines" ]; then
                    lines="$1"
                fi
                shift
                ;;
        esac
    done
    
    echo "=========================================="
    echo "  Jarvis AI Assistant - Logs Viewer"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Запуск просмотра логов"
    
    if [ "$metrics_flag" = true ]; then
        view_metrics
    elif [ "$system_flag" = true ]; then
        view_system_logs "$lines"
    elif [ "$search_errors_flag" = true ]; then
        search_errors "$service" "$lines"
    elif [ -n "$log_type" ]; then
        view_file_logs "$log_type" "$lines"
    else
        if [ "$follow" = true ]; then
            view_docker_compose_logs "$service" "$lines"
        else
            view_docker_compose_logs "$service" "$lines"
        fi
    fi
    
    log_to_file "SUCCESS: Просмотр логов завершен"
    
    echo
    echo "=========================================="
    echo "  Просмотр логов завершен!"
    echo "=========================================="
    echo
    echo "Для получения справки используйте: $0 --help"
    echo
}

# Запуск основной функции
main "$@"