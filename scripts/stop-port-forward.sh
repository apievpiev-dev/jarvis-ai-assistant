#!/bin/bash

# Скрипт остановки port-forward процессов для Jarvis AI Assistant
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
LOG_FILE="/workspace/jarvis/logs/stop_port_forward.log"

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Остановка port-forward процессов
stop_port_forward_processes() {
    log_info "Остановка port-forward процессов..."
    
    # Поиск и остановка процессов port-forward
    local pids=$(pgrep -f "kubectl port-forward" || true)
    
    if [ -n "$pids" ]; then
        log_info "Найдены процессы port-forward: $pids"
        for pid in $pids; do
            log_info "Остановка процесса: $pid"
            kill $pid 2>/dev/null || true
        done
        log_success "Процессы port-forward остановлены"
        log_to_file "SUCCESS: Процессы port-forward остановлены"
    else
        log_info "Процессы port-forward не найдены"
        log_to_file "INFO: Процессы port-forward не найдены"
    fi
}

# Остановка процессов по PID файлам
stop_pid_file_processes() {
    log_info "Остановка процессов по PID файлам..."
    
    # Поиск PID файлов
    local pid_files=$(find /tmp -name "port-forward-*.pid" 2>/dev/null || true)
    
    if [ -n "$pid_files" ]; then
        for pid_file in $pid_files; do
            if [ -f "$pid_file" ]; then
                local pid=$(cat "$pid_file")
                local service=$(basename "$pid_file" .pid | sed 's/port-forward-//')
                
                log_info "Остановка процесса $service (PID: $pid)"
                kill $pid 2>/dev/null || true
                rm "$pid_file"
            fi
        done
        log_success "Процессы по PID файлам остановлены"
        log_to_file "SUCCESS: Процессы по PID файлам остановлены"
    else
        log_info "PID файлы не найдены"
        log_to_file "INFO: PID файлы не найдены"
    fi
}

# Остановка процессов по портам
stop_port_processes() {
    log_info "Остановка процессов по портам..."
    
    # Список портов для проверки
    local ports=(3000 8000 9090 3001)
    
    for port in "${ports[@]}"; do
        local pid=$(lsof -ti :$port 2>/dev/null || true)
        if [ -n "$pid" ]; then
            log_info "Остановка процесса на порту $port (PID: $pid)"
            kill $pid 2>/dev/null || true
        fi
    done
    
    log_success "Процессы по портам остановлены"
    log_to_file "SUCCESS: Процессы по портам остановлены"
}

# Проверка остановки
verify_stop() {
    log_info "Проверка остановки port-forward процессов..."
    
    # Проверка процессов kubectl port-forward
    local pids=$(pgrep -f "kubectl port-forward" || true)
    if [ -n "$pids" ]; then
        log_warning "Некоторые процессы port-forward все еще работают: $pids"
        log_to_file "WARNING: Некоторые процессы port-forward все еще работают: $pids"
    else
        log_success "Все процессы port-forward остановлены"
        log_to_file "SUCCESS: Все процессы port-forward остановлены"
    fi
    
    # Проверка портов
    local ports=(3000 8000 9090 3001)
    for port in "${ports[@]}"; do
        if lsof -i :$port > /dev/null 2>&1; then
            log_warning "Порт $port все еще занят"
            log_to_file "WARNING: Порт $port все еще занят"
        else
            log_success "Порт $port свободен"
        fi
    done
}

# Очистка временных файлов
cleanup_temp_files() {
    log_info "Очистка временных файлов..."
    
    # Удаление PID файлов
    rm -rf /tmp/port-forward-*.pid 2>/dev/null || true
    
    log_success "Временные файлы очищены"
    log_to_file "SUCCESS: Временные файлы очищены"
}

# Просмотр справки
show_help() {
    echo "Использование: $0 [опции]"
    echo
    echo "Опции:"
    echo "  -h, --help              Показать эту справку"
    echo "  -v, --verify            Проверить статус остановки"
    echo "  -c, --cleanup           Очистить временные файлы"
    echo "  -f, --force             Принудительная остановка"
    echo
    echo "Примеры:"
    echo "  $0                      Остановить все port-forward процессы"
    echo "  $0 -v                   Проверить статус остановки"
    echo "  $0 -c                   Остановить и очистить временные файлы"
    echo "  $0 -f                   Принудительная остановка"
}

# Основная функция
main() {
    local verify_flag=false
    local cleanup_flag=false
    local force_flag=false
    
    # Парсинг аргументов
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verify)
                verify_flag=true
                shift
                ;;
            -c|--cleanup)
                cleanup_flag=true
                shift
                ;;
            -f|--force)
                force_flag=true
                shift
                ;;
            *)
                log_error "Неизвестный аргумент: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo "=========================================="
    echo "  Jarvis AI Assistant - Stop Port Forward"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Начало остановки port-forward процессов"
    
    if [ "$verify_flag" = true ]; then
        verify_stop
    else
        stop_port_forward_processes
        stop_pid_file_processes
        stop_port_processes
        
        if [ "$cleanup_flag" = true ]; then
            cleanup_temp_files
        fi
        
        verify_stop
    fi
    
    log_to_file "SUCCESS: Остановка port-forward процессов завершена"
    
    echo
    echo "=========================================="
    echo "  Port-forward процессы остановлены!"
    echo "=========================================="
    echo
    echo "Для запуска port-forward используйте:"
    echo "  ./scripts/deploy-k8s.sh"
    echo
    echo "Лог остановки: $LOG_FILE"
    echo
}

# Запуск основной функции
main "$@"