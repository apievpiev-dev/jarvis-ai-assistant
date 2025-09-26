#!/bin/bash

# Скрипт установки зависимостей для Jarvis AI Assistant
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
LOG_FILE="/workspace/jarvis/logs/install_dependencies.log"

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Обновление системы
update_system() {
    log_info "Обновление системы..."
    
    if command -v apt &> /dev/null; then
        # Обновление списка пакетов
        sudo apt update
        
        # Обновление установленных пакетов
        sudo apt upgrade -y
        
        log_success "Система обновлена"
        log_to_file "SUCCESS: Система обновлена"
    else
        log_warning "Система не поддерживает apt, пропускаем обновление"
        log_to_file "WARNING: Система не поддерживает apt"
    fi
}

# Установка базовых пакетов
install_basic_packages() {
    log_info "Установка базовых пакетов..."
    
    if command -v apt &> /dev/null; then
        # Установка необходимых пакетов
        sudo apt install -y \
            curl \
            wget \
            git \
            unzip \
            build-essential \
            python3 \
            python3-pip \
            python3-venv \
            nodejs \
            npm \
            docker.io \
            docker-compose \
            postgresql-client \
            redis-tools \
            jq \
            bc \
            htop \
            tree \
            vim \
            nano \
            ufw \
            fail2ban \
            logrotate \
            cron \
            systemd \
            supervisor
        
        log_success "Базовые пакеты установлены"
        log_to_file "SUCCESS: Базовые пакеты установлены"
    else
        log_error "Система не поддерживает apt"
        log_to_file "ERROR: Система не поддерживает apt"
        exit 1
    fi
}

# Настройка Docker
setup_docker() {
    log_info "Настройка Docker..."
    
    # Добавление пользователя в группу docker
    sudo usermod -aG docker $USER
    
    # Запуск и включение Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Проверка установки Docker
    if docker --version &> /dev/null; then
        log_success "Docker настроен успешно"
        log_to_file "SUCCESS: Docker настроен успешно"
    else
        log_error "Ошибка настройки Docker"
        log_to_file "ERROR: Ошибка настройки Docker"
        exit 1
    fi
}

# Настройка Docker Compose
setup_docker_compose() {
    log_info "Настройка Docker Compose..."
    
    # Проверка установки Docker Compose
    if docker-compose --version &> /dev/null; then
        log_success "Docker Compose настроен успешно"
        log_to_file "SUCCESS: Docker Compose настроен успешно"
    else
        log_error "Ошибка настройки Docker Compose"
        log_to_file "ERROR: Ошибка настройки Docker Compose"
        exit 1
    fi
}

# Установка Python зависимостей
install_python_dependencies() {
    log_info "Установка Python зависимостей..."
    
    # Создание виртуального окружения
    python3 -m venv /workspace/jarvis/venv
    source /workspace/jarvis/venv/bin/activate
    
    # Обновление pip
    pip install --upgrade pip
    
    # Установка зависимостей
    pip install \
        fastapi \
        uvicorn \
        websockets \
        pydantic \
        redis \
        celery \
        psycopg2-binary \
        python-multipart \
        python-jose \
        passlib \
        python-crontab \
        httpx \
        aioredis \
        starlette-rate-limiter \
        transformers \
        torch \
        accelerate \
        optimum \
        onnxruntime \
        ctranslate2 \
        sentencepiece \
        pydub \
        soundfile \
        espnet_model_zoo \
        espnet \
        streamlit \
        plotly \
        pandas \
        numpy \
        scikit-learn \
        matplotlib \
        seaborn \
        requests \
        aiofiles \
        python-dotenv \
        pyyaml \
        jinja2 \
        markdown \
        beautifulsoup4 \
        lxml \
        pillow \
        opencv-python \
        face-recognition \
        dlib \
        cmake \
        gcc \
        g++ \
        make
    
    log_success "Python зависимости установлены"
    log_to_file "SUCCESS: Python зависимости установлены"
}

# Установка Node.js зависимостей
install_nodejs_dependencies() {
    log_info "Установка Node.js зависимостей..."
    
    # Переход в директорию web-service
    cd /workspace/jarvis/services/web-service
    
    # Установка зависимостей
    npm install \
        react \
        react-dom \
        react-router-dom \
        axios \
        socket.io-client \
        @mui/material \
        @mui/icons-material \
        @emotion/react \
        @emotion/styled \
        @mui/lab \
        @mui/x-data-grid \
        @mui/x-date-pickers \
        recharts \
        react-query \
        react-hook-form \
        react-hot-toast \
        framer-motion \
        react-spring \
        react-use \
        react-use-gesture \
        react-use-measure \
        react-use-scroll-position \
        react-use-onclickoutside \
        react-use-keypress \
        react-use-debounce \
        react-use-local-storage \
        react-use-session-storage \
        react-use-cookie \
        react-use-clipboard \
        react-use-fetch \
        react-use-websocket \
        react-use-interval \
        react-use-timeout \
        react-use-previous \
        react-use-async \
        react-use-async-effect \
        react-use-async-state \
        react-use-async-callback \
        react-use-async-memo \
        react-use-async-ref \
        react-use-async-effect \
        react-use-async-state \
        react-use-async-callback \
        react-use-async-memo \
        react-use-async-ref
    
    # Возврат в корневую директорию
    cd /workspace/jarvis
    
    log_success "Node.js зависимости установлены"
    log_to_file "SUCCESS: Node.js зависимости установлены"
}

# Настройка файрвола
setup_firewall() {
    log_info "Настройка файрвола..."
    
    # Включение UFW
    sudo ufw --force enable
    
    # Разрешение SSH
    sudo ufw allow ssh
    
    # Разрешение HTTP и HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Разрешение портов для Jarvis
    sudo ufw allow 3000/tcp  # Web Service
    sudo ufw allow 8000/tcp  # API Gateway
    sudo ufw allow 9090/tcp  # Prometheus
    sudo ufw allow 3001/tcp  # Grafana
    
    # Проверка статуса файрвола
    sudo ufw status
    
    log_success "Файрвол настроен"
    log_to_file "SUCCESS: Файрвол настроен"
}

# Настройка fail2ban
setup_fail2ban() {
    log_info "Настройка fail2ban..."
    
    # Создание конфигурации для fail2ban
    sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF
    
    # Перезапуск fail2ban
    sudo systemctl restart fail2ban
    sudo systemctl enable fail2ban
    
    log_success "fail2ban настроен"
    log_to_file "SUCCESS: fail2ban настроен"
}

# Настройка логирования
setup_logging() {
    log_info "Настройка логирования..."
    
    # Создание конфигурации для logrotate
    sudo tee /etc/logrotate.d/jarvis > /dev/null << EOF
/workspace/jarvis/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        /bin/kill -HUP \`cat /var/run/rsyslogd.pid 2> /dev/null\` 2> /dev/null || true
    endscript
}
EOF
    
    log_success "Логирование настроено"
    log_to_file "SUCCESS: Логирование настроено"
}

# Настройка cron задач
setup_cron() {
    log_info "Настройка cron задач..."
    
    # Создание cron задач для Jarvis
    (crontab -l 2>/dev/null; echo "# Jarvis AI Assistant cron tasks") | crontab -
    (crontab -l 2>/dev/null; echo "0 2 * * * /workspace/jarvis/scripts/backup.sh") | crontab -
    (crontab -l 2>/dev/null; echo "0 3 * * * /workspace/jarvis/scripts/cleanup.sh") | crontab -
    (crontab -l 2>/dev/null; echo "*/5 * * * * /workspace/jarvis/scripts/health-check.sh") | crontab -
    (crontab -l 2>/dev/null; echo "0 1 * * 0 /workspace/jarvis/scripts/update.sh") | crontab -
    
    log_success "Cron задачи настроены"
    log_to_file "SUCCESS: Cron задачи настроены"
}

# Настройка systemd сервисов
setup_systemd_services() {
    log_info "Настройка systemd сервисов..."
    
    # Создание сервиса для Jarvis
    sudo tee /etc/systemd/system/jarvis.service > /dev/null << EOF
[Unit]
Description=Jarvis AI Assistant
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/workspace/jarvis
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF
    
    # Перезагрузка systemd
    sudo systemctl daemon-reload
    
    # Включение сервиса
    sudo systemctl enable jarvis.service
    
    log_success "systemd сервисы настроены"
    log_to_file "SUCCESS: systemd сервисы настроены"
}

# Проверка установки
verify_installation() {
    log_info "Проверка установки..."
    
    # Проверка Docker
    if docker --version &> /dev/null; then
        log_success "Docker: $(docker --version)"
    else
        log_error "Docker не установлен"
    fi
    
    # Проверка Docker Compose
    if docker-compose --version &> /dev/null; then
        log_success "Docker Compose: $(docker-compose --version)"
    else
        log_error "Docker Compose не установлен"
    fi
    
    # Проверка Python
    if python3 --version &> /dev/null; then
        log_success "Python: $(python3 --version)"
    else
        log_error "Python не установлен"
    fi
    
    # Проверка Node.js
    if node --version &> /dev/null; then
        log_success "Node.js: $(node --version)"
    else
        log_error "Node.js не установлен"
    fi
    
    # Проверка npm
    if npm --version &> /dev/null; then
        log_success "npm: $(npm --version)"
    else
        log_error "npm не установлен"
    fi
    
    log_to_file "SUCCESS: Проверка установки завершена"
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Install Dependencies"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Начало установки зависимостей"
    
    update_system
    install_basic_packages
    setup_docker
    setup_docker_compose
    install_python_dependencies
    install_nodejs_dependencies
    setup_firewall
    setup_fail2ban
    setup_logging
    setup_cron
    setup_systemd_services
    verify_installation
    
    log_to_file "SUCCESS: Установка зависимостей завершена"
    
    echo
    echo "=========================================="
    echo "  Установка зависимостей завершена!"
    echo "=========================================="
    echo
    echo "Для завершения настройки выполните:"
    echo "  source /workspace/jarvis/venv/bin/activate"
    echo "  ./scripts/setup.sh"
    echo
    echo "Лог установки: $LOG_FILE"
    echo
}

# Запуск основной функции
main "$@"