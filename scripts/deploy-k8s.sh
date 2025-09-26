#!/bin/bash

# Скрипт развертывания Jarvis AI Assistant в Kubernetes
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
    
    # Проверка версии kubectl
    KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3)
    log_info "Версия kubectl: $KUBECTL_VERSION"
    
    log_success "Системные требования проверены"
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
}

# Применение манифестов Kubernetes
apply_manifests() {
    log_info "Применение манифестов Kubernetes..."
    
    # Создание namespace
    kubectl apply -f k8s/namespace.yaml
    
    # Применение всех манифестов
    if command -v kustomize &> /dev/null; then
        log_info "Использование kustomize для применения манифестов..."
        kustomize build k8s/ | kubectl apply -f -
    else
        log_info "Применение манифестов напрямую..."
        kubectl apply -f k8s/
    fi
    
    log_success "Манифесты применены"
}

# Ожидание готовности подов
wait_for_pods() {
    log_info "Ожидание готовности подов..."
    
    # Ожидание готовности всех подов в namespace jarvis
    kubectl wait --for=condition=Ready pod --all -n jarvis --timeout=300s
    
    log_success "Все поды готовы"
}

# Проверка статуса развертывания
check_deployment_status() {
    log_info "Проверка статуса развертывания..."
    
    # Проверка подов
    log_info "Статус подов:"
    kubectl get pods -n jarvis
    
    # Проверка сервисов
    log_info "Статус сервисов:"
    kubectl get services -n jarvis
    
    # Проверка ingress
    log_info "Статус ingress:"
    kubectl get ingress -n jarvis
    
    log_success "Проверка статуса завершена"
}

# Настройка портов для доступа
setup_port_forwarding() {
    log_info "Настройка портов для локального доступа..."
    
    # Функция для запуска port-forward в фоне
    start_port_forward() {
        local service=$1
        local local_port=$2
        local service_port=$3
        
        log_info "Настройка порта $local_port -> $service:$service_port"
        kubectl port-forward -n jarvis service/$service $local_port:$service_port &
        echo $! > /tmp/port-forward-$service.pid
    }
    
    # Настройка портов для основных сервисов
    start_port_forward "web-service" 3000 3000
    start_port_forward "api-gateway" 8000 8000
    start_port_forward "grafana" 3001 3000
    start_port_forward "prometheus" 9090 9090
    
    log_success "Порты настроены"
    log_info "Веб-интерфейс: http://localhost:3000"
    log_info "API Gateway: http://localhost:8000"
    log_info "Grafana: http://localhost:3001"
    log_info "Prometheus: http://localhost:9090"
}

# Создание скриптов управления
create_management_scripts() {
    log_info "Создание скриптов управления Kubernetes..."
    
    # Скрипт остановки port-forward
    cat > scripts/stop-port-forward.sh << 'EOF'
#!/bin/bash
echo "Остановка port-forward процессов..."
for pid_file in /tmp/port-forward-*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        kill $pid 2>/dev/null || true
        rm "$pid_file"
    fi
done
echo "Port-forward процессы остановлены"
EOF
    
    # Скрипт просмотра логов
    cat > scripts/k8s-logs.sh << 'EOF'
#!/bin/bash
if [ -z "$1" ]; then
    echo "Просмотр логов всех подов..."
    kubectl logs -f -l app.kubernetes.io/name=jarvis -n jarvis
else
    echo "Просмотр логов пода: $1"
    kubectl logs -f "$1" -n jarvis
fi
EOF
    
    # Скрипт масштабирования
    cat > scripts/scale.sh << 'EOF'
#!/bin/bash
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Использование: $0 <deployment> <replicas>"
    echo "Пример: $0 api-gateway 3"
    exit 1
fi

deployment=$1
replicas=$2

echo "Масштабирование $deployment до $replicas реплик..."
kubectl scale deployment "$deployment" --replicas="$replicas" -n jarvis
echo "Масштабирование завершено"
EOF
    
    # Скрипт обновления
    cat > scripts/k8s-update.sh << 'EOF'
#!/bin/bash
echo "Обновление Jarvis AI Assistant в Kubernetes..."

# Сборка новых образов
echo "Сборка новых образов..."
services=("api-gateway" "voice-service" "brain-service" "task-service" "web-service" "code-service" "learning-service")

for service in "${services[@]}"; do
    echo "Сборка $service..."
    docker build -t jarvis/$service:latest ./services/$service/
done

# Применение обновлений
echo "Применение обновлений..."
kubectl rollout restart deployment -n jarvis

# Ожидание готовности
echo "Ожидание готовности подов..."
kubectl rollout status deployment -n jarvis

echo "Обновление завершено"
EOF
    
    # Скрипт удаления
    cat > scripts/k8s-delete.sh << 'EOF'
#!/bin/bash
echo "Удаление Jarvis AI Assistant из Kubernetes..."

# Остановка port-forward
./scripts/stop-port-forward.sh

# Удаление ресурсов
if command -v kustomize &> /dev/null; then
    kustomize build k8s/ | kubectl delete -f -
else
    kubectl delete -f k8s/
fi

echo "Jarvis AI Assistant удален из Kubernetes"
EOF
    
    # Делаем скрипты исполняемыми
    chmod +x scripts/*.sh
    
    log_success "Скрипты управления созданы"
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Kubernetes Deploy"
    echo "=========================================="
    echo
    
    check_requirements
    build_images
    apply_manifests
    wait_for_pods
    check_deployment_status
    setup_port_forwarding
    create_management_scripts
    
    echo
    echo "=========================================="
    echo "  Развертывание завершено!"
    echo "=========================================="
    echo
    echo "Веб-интерфейс: http://localhost:3000"
    echo "API Gateway: http://localhost:8000"
    echo "Grafana: http://localhost:3001"
    echo "Prometheus: http://localhost:9090"
    echo
    echo "Управление:"
    echo "  Логи: ./scripts/k8s-logs.sh"
    echo "  Масштабирование: ./scripts/scale.sh <deployment> <replicas>"
    echo "  Обновление: ./scripts/k8s-update.sh"
    echo "  Удаление: ./scripts/k8s-delete.sh"
    echo "  Остановка портов: ./scripts/stop-port-forward.sh"
    echo
    echo "Проверка статуса:"
    echo "  kubectl get pods -n jarvis"
    echo "  kubectl get services -n jarvis"
    echo
}

# Запуск основной функции
main "$@"