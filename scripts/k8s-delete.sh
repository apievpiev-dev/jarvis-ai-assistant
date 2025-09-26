#!/bin/bash

# Скрипт удаления Jarvis AI Assistant из Kubernetes
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
LOG_FILE="/workspace/jarvis/logs/k8s_delete.log"

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Проверка системных требований
check_requirements() {
    log_info "Проверка системных требований..."
    
    # Проверка kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl не установлен. Установите kubectl и попробуйте снова."
        exit 1
    fi
    
    # Проверка подключения к кластеру
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Нет подключения к Kubernetes кластеру. Проверьте настройки kubectl."
        exit 1
    fi
    
    # Проверка namespace
    if ! kubectl get namespace jarvis &> /dev/null; then
        log_warning "Namespace jarvis не найден. Приложение уже удалено."
        exit 0
    fi
    
    log_success "Системные требования проверены"
    log_to_file "SUCCESS: Системные требования проверены"
}

# Остановка port-forward процессов
stop_port_forward() {
    log_info "Остановка port-forward процессов..."
    
    for pid_file in /tmp/port-forward-*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            kill $pid 2>/dev/null || true
            rm "$pid_file"
        fi
    done
    
    log_success "Port-forward процессы остановлены"
    log_to_file "SUCCESS: Port-forward процессы остановлены"
}

# Удаление ресурсов Kubernetes
delete_kubernetes_resources() {
    log_info "Удаление ресурсов Kubernetes..."
    
    # Удаление всех ресурсов в namespace jarvis
    if command -v kustomize &> /dev/null; then
        log_info "Использование kustomize для удаления ресурсов..."
        kustomize build k8s/ | kubectl delete -f - 2>/dev/null || true
    else
        log_info "Удаление ресурсов напрямую..."
        kubectl delete -f k8s/ 2>/dev/null || true
    fi
    
    # Удаление namespace
    kubectl delete namespace jarvis 2>/dev/null || true
    
    log_success "Ресурсы Kubernetes удалены"
    log_to_file "SUCCESS: Ресурсы Kubernetes удалены"
}

# Очистка Docker образов
cleanup_docker_images() {
    log_info "Очистка Docker образов..."
    
    # Удаление образов Jarvis
    docker images | grep jarvis | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true
    
    # Очистка неиспользуемых образов
    docker image prune -f
    
    log_success "Docker образы очищены"
    log_to_file "SUCCESS: Docker образы очищены"
}

# Очистка временных файлов
cleanup_temp_files() {
    log_info "Очистка временных файлов..."
    
    # Удаление временных файлов
    rm -rf /tmp/port-forward-*.pid 2>/dev/null || true
    rm -rf /workspace/jarvis/update_temp 2>/dev/null || true
    rm -rf /workspace/jarvis/restore_temp 2>/dev/null || true
    
    log_success "Временные файлы очищены"
    log_to_file "SUCCESS: Временные файлы очищены"
}

# Проверка удаления
verify_deletion() {
    log_info "Проверка удаления..."
    
    # Проверка namespace
    if kubectl get namespace jarvis &> /dev/null; then
        log_warning "Namespace jarvis все еще существует"
        log_to_file "WARNING: Namespace jarvis все еще существует"
    else
        log_success "Namespace jarvis удален"
        log_to_file "SUCCESS: Namespace jarvis удален"
    fi
    
    # Проверка подов
    pods=$(kubectl get pods -n jarvis 2>/dev/null | wc -l)
    if [ "$pods" -gt 1 ]; then
        log_warning "Некоторые поды все еще существуют"
        log_to_file "WARNING: Некоторые поды все еще существуют"
    else
        log_success "Все поды удалены"
        log_to_file "SUCCESS: Все поды удалены"
    fi
    
    # Проверка сервисов
    services=$(kubectl get services -n jarvis 2>/dev/null | wc -l)
    if [ "$services" -gt 1 ]; then
        log_warning "Некоторые сервисы все еще существуют"
        log_to_file "WARNING: Некоторые сервисы все еще существуют"
    else
        log_success "Все сервисы удалены"
        log_to_file "SUCCESS: Все сервисы удалены"
    fi
}

# Создание бэкапа перед удалением
create_backup_before_deletion() {
    log_info "Создание бэкапа перед удалением..."
    
    if [ -f "scripts/backup.sh" ]; then
        ./scripts/backup.sh
        log_success "Бэкап создан перед удалением"
        log_to_file "SUCCESS: Бэкап создан перед удалением"
    else
        log_warning "Скрипт бэкапа не найден, пропускаем создание бэкапа"
        log_to_file "WARNING: Скрипт бэкапа не найден"
    fi
}

# Подтверждение удаления
confirm_deletion() {
    log_warning "ВНИМАНИЕ: Это действие удалит все ресурсы Jarvis AI Assistant из Kubernetes!"
    log_warning "Все данные будут потеряны, если не создан бэкап!"
    
    read -p "Вы уверены, что хотите продолжить? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Удаление отменено пользователем"
        log_to_file "INFO: Удаление отменено пользователем"
        exit 0
    fi
    
    log_info "Удаление подтверждено пользователем"
    log_to_file "INFO: Удаление подтверждено пользователем"
}

# Просмотр справки
show_help() {
    echo "Использование: $0 [опции]"
    echo
    echo "Опции:"
    echo "  -h, --help              Показать эту справку"
    echo "  -f, --force             Принудительное удаление без подтверждения"
    echo "  -b, --backup            Создать бэкап перед удалением"
    echo "  -c, --cleanup           Очистить Docker образы и временные файлы"
    echo "  -v, --verify            Проверить статус удаления"
    echo
    echo "Примеры:"
    echo "  $0                      Удалить с подтверждением"
    echo "  $0 -f                   Принудительное удаление"
    echo "  $0 -b                   Создать бэкап и удалить"
    echo "  $0 -c                   Удалить и очистить все"
    echo "  $0 -v                   Проверить статус удаления"
}

# Основная функция
main() {
    local force_flag=false
    local backup_flag=false
    local cleanup_flag=false
    local verify_flag=false
    
    # Парсинг аргументов
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -f|--force)
                force_flag=true
                shift
                ;;
            -b|--backup)
                backup_flag=true
                shift
                ;;
            -c|--cleanup)
                cleanup_flag=true
                shift
                ;;
            -v|--verify)
                verify_flag=true
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
    echo "  Jarvis AI Assistant - Kubernetes Delete"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Начало удаления из Kubernetes"
    
    if [ "$verify_flag" = true ]; then
        verify_deletion
    else
        check_requirements
        
        if [ "$force_flag" = false ]; then
            confirm_deletion
        fi
        
        if [ "$backup_flag" = true ]; then
            create_backup_before_deletion
        fi
        
        stop_port_forward
        delete_kubernetes_resources
        
        if [ "$cleanup_flag" = true ]; then
            cleanup_docker_images
            cleanup_temp_files
        fi
        
        verify_deletion
    fi
    
    log_to_file "SUCCESS: Удаление из Kubernetes завершено"
    
    echo
    echo "=========================================="
    echo "  Удаление завершено!"
    echo "=========================================="
    echo
    echo "Для повторного развертывания используйте:"
    echo "  ./scripts/deploy-k8s.sh"
    echo
    echo "Лог удаления: $LOG_FILE"
    echo
}

# Запуск основной функции
main "$@"