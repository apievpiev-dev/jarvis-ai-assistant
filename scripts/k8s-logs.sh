#!/bin/bash

# Скрипт просмотра логов Kubernetes для Jarvis AI Assistant
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
LOG_FILE="/workspace/jarvis/logs/k8s_logs.log"

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Просмотр логов всех подов
view_all_pods_logs() {
    local lines="${1:-100}"
    
    log_info "Просмотр логов всех подов..."
    
    # Получение списка подов
    local pods=$(kubectl get pods -n jarvis -o name | sed 's/pod\///')
    
    if [ -z "$pods" ]; then
        log_warning "Поды не найдены в namespace jarvis"
        return 1
    fi
    
    # Просмотр логов каждого пода
    for pod in $pods; do
        log_info "Логи пода: $pod"
        kubectl logs -n jarvis "$pod" --tail="$lines"
        echo "----------------------------------------"
    done
    
    log_to_file "INFO: Просмотр логов всех подов завершен"
}

# Просмотр логов конкретного пода
view_pod_logs() {
    local pod="$1"
    local lines="${2:-100}"
    
    log_info "Просмотр логов пода: $pod..."
    
    if kubectl get pod "$pod" -n jarvis &> /dev/null; then
        kubectl logs -n jarvis "$pod" --tail="$lines"
        log_success "Логи пода $pod просмотрены"
        log_to_file "SUCCESS: Логи пода $pod просмотрены"
    else
        log_error "Под $pod не найден в namespace jarvis"
        log_to_file "ERROR: Под $pod не найден"
        return 1
    fi
}

# Просмотр логов по селектору
view_logs_by_selector() {
    local selector="$1"
    local lines="${2:-100}"
    
    log_info "Просмотр логов по селектору: $selector..."
    
    # Получение подов по селектору
    local pods=$(kubectl get pods -n jarvis -l "$selector" -o name | sed 's/pod\///')
    
    if [ -z "$pods" ]; then
        log_warning "Поды не найдены по селектору: $selector"
        return 1
    fi
    
    # Просмотр логов каждого пода
    for pod in $pods; do
        log_info "Логи пода: $pod"
        kubectl logs -n jarvis "$pod" --tail="$lines"
        echo "----------------------------------------"
    done
    
    log_to_file "INFO: Просмотр логов по селектору $selector завершен"
}

# Слежение за логами в реальном времени
follow_logs() {
    local pod="$1"
    local lines="${2:-100}"
    
    log_info "Слежение за логами пода: $pod..."
    
    if kubectl get pod "$pod" -n jarvis &> /dev/null; then
        kubectl logs -n jarvis "$pod" --tail="$lines" -f
        log_success "Слежение за логами пода $pod завершено"
        log_to_file "SUCCESS: Слежение за логами пода $pod завершено"
    else
        log_error "Под $pod не найден в namespace jarvis"
        log_to_file "ERROR: Под $pod не найден"
        return 1
    fi
}

# Поиск ошибок в логах
search_errors() {
    local pod="$1"
    local lines="${2:-1000}"
    
    log_info "Поиск ошибок в логах пода: $pod..."
    
    if kubectl get pod "$pod" -n jarvis &> /dev/null; then
        kubectl logs -n jarvis "$pod" --tail="$lines" 2>&1 | grep -i "error\|exception\|failed\|critical\|fatal" || log_info "Ошибок не найдено"
        log_success "Поиск ошибок в логах пода $pod завершен"
        log_to_file "SUCCESS: Поиск ошибок в логах пода $pod завершен"
    else
        log_error "Под $pod не найден в namespace jarvis"
        log_to_file "ERROR: Под $pod не найден"
        return 1
    fi
}

# Просмотр событий
view_events() {
    local lines="${1:-100}"
    
    log_info "Просмотр событий namespace jarvis..."
    
    kubectl get events -n jarvis --sort-by='.lastTimestamp' | tail -n "$lines"
    
    log_success "События namespace jarvis просмотрены"
    log_to_file "SUCCESS: События namespace jarvis просмотрены"
}

# Просмотр статуса подов
view_pods_status() {
    log_info "Просмотр статуса подов..."
    
    kubectl get pods -n jarvis -o wide
    
    log_success "Статус подов просмотрен"
    log_to_file "SUCCESS: Статус подов просмотрен"
}

# Просмотр описания пода
describe_pod() {
    local pod="$1"
    
    log_info "Просмотр описания пода: $pod..."
    
    if kubectl get pod "$pod" -n jarvis &> /dev/null; then
        kubectl describe pod "$pod" -n jarvis
        log_success "Описание пода $pod просмотрено"
        log_to_file "SUCCESS: Описание пода $pod просмотрено"
    else
        log_error "Под $pod не найден в namespace jarvis"
        log_to_file "ERROR: Под $pod не найден"
        return 1
    fi
}

# Просмотр справки
show_help() {
    echo "Использование: $0 [опции] [под] [количество_строк]"
    echo
    echo "Опции:"
    echo "  -h, --help              Показать эту справку"
    echo "  -f, --follow            Следить за логами в реальном времени"
    echo "  -e, --errors            Поиск ошибок в логах"
    echo "  -s, --selector <селектор>  Просмотр логов по селектору"
    echo "  -a, --all               Просмотр логов всех подов"
    echo "  -v, --events            Просмотр событий"
    echo "  -p, --pods              Просмотр статуса подов"
    echo "  -d, --describe          Просмотр описания пода"
    echo
    echo "Примеры:"
    echo "  $0                      Просмотр логов всех подов"
    echo "  $0 api-gateway-xxx      Просмотр логов конкретного пода"
    echo "  $0 -f web-service-xxx   Следить за логами в реальном времени"
    echo "  $0 -e api-gateway-xxx   Поиск ошибок в логах"
    echo "  $0 -s app=api-gateway   Просмотр логов по селектору"
    echo "  $0 -a                   Просмотр логов всех подов"
    echo "  $0 -v                   Просмотр событий"
    echo "  $0 -p                   Просмотр статуса подов"
    echo "  $0 -d api-gateway-xxx   Просмотр описания пода"
}

# Основная функция
main() {
    local follow_flag=false
    local search_errors_flag=false
    local selector=""
    local all_flag=false
    local events_flag=false
    local pods_flag=false
    local describe_flag=false
    local pod=""
    local lines=100
    
    # Парсинг аргументов
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -f|--follow)
                follow_flag=true
                shift
                ;;
            -e|--errors)
                search_errors_flag=true
                shift
                ;;
            -s|--selector)
                selector="$2"
                shift 2
                ;;
            -a|--all)
                all_flag=true
                shift
                ;;
            -v|--events)
                events_flag=true
                shift
                ;;
            -p|--pods)
                pods_flag=true
                shift
                ;;
            -d|--describe)
                describe_flag=true
                shift
                ;;
            *)
                if [ -z "$pod" ]; then
                    pod="$1"
                elif [ -z "$lines" ]; then
                    lines="$1"
                fi
                shift
                ;;
        esac
    done
    
    echo "=========================================="
    echo "  Jarvis AI Assistant - Kubernetes Logs"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Запуск просмотра логов Kubernetes"
    
    if [ "$events_flag" = true ]; then
        view_events "$lines"
    elif [ "$pods_flag" = true ]; then
        view_pods_status
    elif [ "$describe_flag" = true ]; then
        if [ -z "$pod" ]; then
            log_error "Не указан под для описания"
            show_help
            exit 1
        fi
        describe_pod "$pod"
    elif [ "$all_flag" = true ]; then
        view_all_pods_logs "$lines"
    elif [ -n "$selector" ]; then
        view_logs_by_selector "$selector" "$lines"
    elif [ "$search_errors_flag" = true ]; then
        if [ -z "$pod" ]; then
            log_error "Не указан под для поиска ошибок"
            show_help
            exit 1
        fi
        search_errors "$pod" "$lines"
    elif [ "$follow_flag" = true ]; then
        if [ -z "$pod" ]; then
            log_error "Не указан под для слежения"
            show_help
            exit 1
        fi
        follow_logs "$pod" "$lines"
    else
        if [ -z "$pod" ]; then
            view_all_pods_logs "$lines"
        else
            view_pod_logs "$pod" "$lines"
        fi
    fi
    
    log_to_file "SUCCESS: Просмотр логов Kubernetes завершен"
    
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