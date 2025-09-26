#!/bin/bash

# Скрипт обновления Jarvis AI Assistant в Kubernetes
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
LOG_FILE="/workspace/jarvis/logs/k8s_update.log"

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
    
    # Проверка kustomize
    if ! command -v kustomize &> /dev/null; then
        log_warning "kustomize не установлен. Установите kustomize для лучшей поддержки."
    fi
    
    # Проверка подключения к кластеру
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Нет подключения к Kubernetes кластеру. Проверьте настройки kubectl."
        exit 1
    fi
    
    # Проверка namespace
    if ! kubectl get namespace jarvis &> /dev/null; then
        log_error "Namespace jarvis не найден. Сначала разверните приложение."
        exit 1
    fi
    
    log_success "Системные требования проверены"
    log_to_file "SUCCESS: Системные требования проверены"
}

# Сборка Docker образов
build_images() {
    log_info "Сборка Docker образов..."
    
    # Список сервисов для сборки
    services=("api-gateway" "voice-service" "brain-service" "task-service" "web-service" "code-service" "learning-service")
    
    for service in "${services[@]}"; do
        log_info "Сборка образа для $service..."
        docker build -t jarvis/$service:latest ./services/$service/
    done
    
    log_success "Docker образы собраны"
    log_to_file "SUCCESS: Docker образы собраны"
}

# Обновление deployment
update_deployment() {
    local deployment="$1"
    
    log_info "Обновление deployment: $deployment..."
    
    if kubectl get deployment "$deployment" -n jarvis &> /dev/null; then
        kubectl rollout restart deployment "$deployment" -n jarvis
        log_success "Deployment $deployment обновлен"
        log_to_file "SUCCESS: Deployment $deployment обновлен"
    else
        log_error "Deployment $deployment не найден"
        log_to_file "ERROR: Deployment $deployment не найден"
        return 1
    fi
}

# Ожидание готовности deployment
wait_for_deployment() {
    local deployment="$1"
    
    log_info "Ожидание готовности deployment: $deployment..."
    
    if kubectl get deployment "$deployment" -n jarvis &> /dev/null; then
        kubectl rollout status deployment "$deployment" -n jarvis
        log_success "Deployment $deployment готов"
        log_to_file "SUCCESS: Deployment $deployment готов"
    else
        log_error "Deployment $deployment не найден"
        log_to_file "ERROR: Deployment $deployment не найден"
        return 1
    fi
}

# Обновление всех deployment
update_all_deployments() {
    log_info "Обновление всех deployment..."
    
    # Список deployment для обновления
    deployments=("api-gateway" "voice-service" "brain-service" "task-service" "web-service" "code-service" "learning-service")
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" -n jarvis &> /dev/null; then
            update_deployment "$deployment"
            wait_for_deployment "$deployment"
        else
            log_warning "Deployment $deployment не найден, пропускаем"
        fi
    done
    
    log_success "Все deployment обновлены"
    log_to_file "SUCCESS: Все deployment обновлены"
}

# Проверка статуса обновления
check_update_status() {
    log_info "Проверка статуса обновления..."
    
    # Проверка подов
    log_info "Статус подов:"
    kubectl get pods -n jarvis
    
    # Проверка deployment
    log_info "Статус deployment:"
    kubectl get deployments -n jarvis
    
    # Проверка сервисов
    log_info "Статус сервисов:"
    kubectl get services -n jarvis
    
    log_success "Проверка статуса обновления завершена"
    log_to_file "SUCCESS: Проверка статуса обновления завершена"
}

# Проверка работоспособности
verify_functionality() {
    log_info "Проверка работоспособности после обновления..."
    
    # Проверка доступности веб-интерфейса
    if curl -s http://localhost:3000 > /dev/null; then
        log_success "Веб-интерфейс доступен"
    else
        log_warning "Веб-интерфейс недоступен"
    fi
    
    # Проверка API Gateway
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "API Gateway доступен"
    else
        log_warning "API Gateway недоступен"
    fi
    
    # Проверка базы данных
    if kubectl exec -n jarvis deployment/postgres -- pg_isready -U jarvis -d jarvis_db &> /dev/null; then
        log_success "База данных доступна"
    else
        log_warning "База данных недоступна"
    fi
    
    # Проверка Redis
    if kubectl exec -n jarvis deployment/redis -- redis-cli ping &> /dev/null; then
        log_success "Redis доступен"
    else
        log_warning "Redis недоступен"
    fi
    
    log_to_file "SUCCESS: Проверка работоспособности завершена"
}

# Откат обновления
rollback_update() {
    local deployment="$1"
    
    log_info "Откат обновления deployment: $deployment..."
    
    if kubectl get deployment "$deployment" -n jarvis &> /dev/null; then
        kubectl rollout undo deployment "$deployment" -n jarvis
        log_success "Deployment $deployment откачен"
        log_to_file "SUCCESS: Deployment $deployment откачен"
    else
        log_error "Deployment $deployment не найден"
        log_to_file "ERROR: Deployment $deployment не найден"
        return 1
    fi
}

# Откат всех deployment
rollback_all_deployments() {
    log_info "Откат всех deployment..."
    
    # Список deployment для отката
    deployments=("api-gateway" "voice-service" "brain-service" "task-service" "web-service" "code-service" "learning-service")
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" -n jarvis &> /dev/null; then
            rollback_update "$deployment"
        else
            log_warning "Deployment $deployment не найден, пропускаем"
        fi
    done
    
    log_success "Все deployment откачены"
    log_to_file "SUCCESS: Все deployment откачены"
}

# Просмотр справки
show_help() {
    echo "Использование: $0 [опции] [deployment]"
    echo
    echo "Опции:"
    echo "  -h, --help              Показать эту справку"
    echo "  -a, --all               Обновить все deployment"
    echo "  -r, --rollback          Откатить обновление"
    echo "  -s, --status            Проверить статус обновления"
    echo "  -v, --verify            Проверить работоспособность"
    echo
    echo "Deployment:"
    echo "  api-gateway             API Gateway"
    echo "  voice-service           Voice Service"
    echo "  brain-service           Brain Service"
    echo "  task-service            Task Service"
    echo "  web-service             Web Service"
    echo "  code-service            Code Service"
    echo "  learning-service        Learning Service"
    echo
    echo "Примеры:"
    echo "  $0                      Обновить все deployment"
    echo "  $0 -a                   Обновить все deployment"
    echo "  $0 api-gateway          Обновить конкретный deployment"
    echo "  $0 -r api-gateway       Откатить конкретный deployment"
    echo "  $0 -r -a                Откатить все deployment"
    echo "  $0 -s                   Проверить статус обновления"
    echo "  $0 -v                   Проверить работоспособность"
}

# Основная функция
main() {
    local all_flag=false
    local rollback_flag=false
    local status_flag=false
    local verify_flag=false
    local deployment=""
    
    # Парсинг аргументов
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -a|--all)
                all_flag=true
                shift
                ;;
            -r|--rollback)
                rollback_flag=true
                shift
                ;;
            -s|--status)
                status_flag=true
                shift
                ;;
            -v|--verify)
                verify_flag=true
                shift
                ;;
            *)
                if [ -z "$deployment" ]; then
                    deployment="$1"
                fi
                shift
                ;;
        esac
    done
    
    echo "=========================================="
    echo "  Jarvis AI Assistant - Kubernetes Update"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Начало обновления в Kubernetes"
    
    check_requirements
    
    if [ "$status_flag" = true ]; then
        check_update_status
    elif [ "$verify_flag" = true ]; then
        verify_functionality
    elif [ "$rollback_flag" = true ]; then
        if [ "$all_flag" = true ]; then
            rollback_all_deployments
        else
            if [ -z "$deployment" ]; then
                log_error "Не указан deployment для отката"
                show_help
                exit 1
            fi
            rollback_update "$deployment"
        fi
    else
        build_images
        
        if [ "$all_flag" = true ]; then
            update_all_deployments
        else
            if [ -z "$deployment" ]; then
                update_all_deployments
            else
                update_deployment "$deployment"
                wait_for_deployment "$deployment"
            fi
        fi
        
        check_update_status
        verify_functionality
    fi
    
    log_to_file "SUCCESS: Обновление в Kubernetes завершено"
    
    echo
    echo "=========================================="
    echo "  Обновление завершено!"
    echo "=========================================="
    echo
    echo "Проверка статуса:"
    echo "  kubectl get pods -n jarvis"
    echo "  kubectl get deployments -n jarvis"
    echo "  kubectl get services -n jarvis"
    echo
    echo "Лог обновления: $LOG_FILE"
    echo
}

# Запуск основной функции
main "$@"