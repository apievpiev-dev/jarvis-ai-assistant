#!/bin/bash

# Скрипт остановки Jarvis AI Assistant
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
LOG_FILE="/workspace/jarvis/logs/stop.log"

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Остановка Docker Compose сервисов
stop_docker_compose() {
    log_info "Остановка Docker Compose сервисов..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
        log_success "Docker Compose сервисы остановлены"
        log_to_file "SUCCESS: Docker Compose сервисы остановлены"
    else
        log_warning "docker-compose.yml не найден"
        log_to_file "WARNING: docker-compose.yml не найден"
    fi
}

# Остановка Kubernetes сервисов
stop_kubernetes() {
    log_info "Остановка Kubernetes сервисов..."
    
    if kubectl get namespace jarvis &> /dev/null; then
        kubectl delete -f k8s/ 2>/dev/null || true
        log_success "Kubernetes сервисы остановлены"
        log_to_file "SUCCESS: Kubernetes сервисы остановлены"
    else
        log_info "Kubernetes namespace jarvis не найден"
        log_to_file "INFO: Kubernetes namespace jarvis не найден"
    fi
}

# Остановка портов
stop_ports() {
    log_info "Остановка портов..."
    
    # Остановка port-forward процессов
    for pid_file in /tmp/port-forward-*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            kill $pid 2>/dev/null || true
            rm "$pid_file"
        fi
    done
    
    log_success "Порты остановлены"
    log_to_file "SUCCESS: Порты остановлены"
}

# Остановка systemd сервисов
stop_systemd_services() {
    log_info "Остановка systemd сервисов..."
    
    if systemctl is-active --quiet jarvis.service; then
        sudo systemctl stop jarvis.service
        log_success "systemd сервис jarvis остановлен"
        log_to_file "SUCCESS: systemd сервис jarvis остановлен"
    else
        log_info "systemd сервис jarvis не активен"
        log_to_file "INFO: systemd сервис jarvis не активен"
    fi
}

# Остановка cron задач
stop_cron_tasks() {
    log_info "Остановка cron задач..."
    
    # Удаление cron задач Jarvis
    crontab -l 2>/dev/null | grep -v "Jarvis AI Assistant" | crontab - 2>/dev/null || true
    
    log_success "Cron задачи остановлены"
    log_to_file "SUCCESS: Cron задачи остановлены"
}

# Остановка мониторинга
stop_monitoring() {
    log_info "Остановка мониторинга..."
    
    # Остановка Prometheus
    if pgrep -f "prometheus" > /dev/null; then
        pkill -f "prometheus"
        log_info "Prometheus остановлен"
    fi
    
    # Остановка Grafana
    if pgrep -f "grafana" > /dev/null; then
        pkill -f "grafana"
        log_info "Grafana остановлен"
    fi
    
    log_success "Мониторинг остановлен"
    log_to_file "SUCCESS: Мониторинг остановлен"
}

# Остановка Telegram бота
stop_telegram_bot() {
    log_info "Остановка Telegram бота..."
    
    # Остановка Telegram бота
    if pgrep -f "telegram-bot.sh" > /dev/null; then
        pkill -f "telegram-bot.sh"
        log_info "Telegram бот остановлен"
    fi
    
    log_success "Telegram бот остановлен"
    log_to_file "SUCCESS: Telegram бот остановлен"
}

# Проверка остановки
verify_stop() {
    log_info "Проверка остановки..."
    
    # Проверка Docker контейнеров
    containers=$(docker ps -q --filter "name=jarvis")
    if [ -z "$containers" ]; then
        log_success "Все Docker контейнеры остановлены"
    else
        log_warning "Некоторые Docker контейнеры все еще работают"
        docker ps --filter "name=jarvis"
    fi
    
    # Проверка портов
    ports=(3000 8000 9090 3001)
    for port in "${ports[@]}"; do
        if lsof -i :$port > /dev/null 2>&1; then
            log_warning "Порт $port все еще занят"
        else
            log_success "Порт $port свободен"
        fi
    done
    
    log_to_file "SUCCESS: Проверка остановки завершена"
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Stop Script"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Начало остановки Jarvis AI Assistant"
    
    stop_docker_compose
    stop_kubernetes
    stop_ports
    stop_systemd_services
    stop_cron_tasks
    stop_monitoring
    stop_telegram_bot
    verify_stop
    
    log_to_file "SUCCESS: Jarvis AI Assistant остановлен"
    
    echo
    echo "=========================================="
    echo "  Jarvis AI Assistant остановлен!"
    echo "=========================================="
    echo
    echo "Для запуска используйте:"
    echo "  ./scripts/start.sh"
    echo "  ./scripts/quick-start.sh"
    echo
    echo "Лог остановки: $LOG_FILE"
    echo
}

# Запуск основной функции
main "$@"