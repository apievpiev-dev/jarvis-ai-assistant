#!/bin/bash

# Скрипт резервного копирования Jarvis AI Assistant
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
BACKUP_DIR="/workspace/jarvis/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="jarvis_backup_$DATE"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Создание директории для бэкапов
create_backup_dir() {
    log_info "Создание директории для бэкапов..."
    mkdir -p "$BACKUP_PATH"
    log_success "Директория создана: $BACKUP_PATH"
}

# Бэкап базы данных PostgreSQL
backup_database() {
    log_info "Создание бэкапа базы данных..."
    
    # Проверка доступности PostgreSQL
    if ! docker-compose exec -T postgres pg_isready -U jarvis -d jarvis_db &> /dev/null; then
        log_warning "PostgreSQL недоступен, пропускаем бэкап БД"
        return
    fi
    
    # Создание бэкапа
    docker-compose exec -T postgres pg_dump -U jarvis -d jarvis_db > "$BACKUP_PATH/database.sql"
    
    if [ $? -eq 0 ]; then
        log_success "Бэкап базы данных создан"
    else
        log_error "Ошибка создания бэкапа базы данных"
    fi
}

# Бэкап конфигурационных файлов
backup_configs() {
    log_info "Создание бэкапа конфигураций..."
    
    # Создание директории для конфигов
    mkdir -p "$BACKUP_PATH/configs"
    
    # Копирование конфигураций
    cp -r shared/config/* "$BACKUP_PATH/configs/" 2>/dev/null || true
    cp docker-compose.yml "$BACKUP_PATH/" 2>/dev/null || true
    cp docker-compose.prod.yml "$BACKUP_PATH/" 2>/dev/null || true
    cp .env "$BACKUP_PATH/" 2>/dev/null || true
    
    log_success "Бэкап конфигураций создан"
}

# Бэкап логов
backup_logs() {
    log_info "Создание бэкапа логов..."
    
    # Создание директории для логов
    mkdir -p "$BACKUP_PATH/logs"
    
    # Копирование логов
    if [ -d "logs" ]; then
        cp -r logs/* "$BACKUP_PATH/logs/" 2>/dev/null || true
        log_success "Бэкап логов создан"
    else
        log_warning "Директория логов не найдена"
    fi
}

# Бэкап моделей ИИ
backup_models() {
    log_info "Создание бэкапа моделей ИИ..."
    
    # Создание директории для моделей
    mkdir -p "$BACKUP_PATH/models"
    
    # Копирование моделей
    if [ -d "shared/models" ]; then
        cp -r shared/models/* "$BACKUP_PATH/models/" 2>/dev/null || true
        log_success "Бэкап моделей создан"
    else
        log_warning "Директория моделей не найдена"
    fi
}

# Бэкап данных обучения
backup_learning_data() {
    log_info "Создание бэкапа данных обучения..."
    
    # Создание директории для данных обучения
    mkdir -p "$BACKUP_PATH/learning"
    
    # Копирование данных обучения
    if [ -d "shared/memory" ]; then
        cp -r shared/memory/* "$BACKUP_PATH/learning/" 2>/dev/null || true
        log_success "Бэкап данных обучения создан"
    else
        log_warning "Директория данных обучения не найдена"
    fi
}

# Создание архива
create_archive() {
    log_info "Создание архива бэкапа..."
    
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    
    if [ $? -eq 0 ]; then
        log_success "Архив создан: ${BACKUP_NAME}.tar.gz"
        # Удаление временной директории
        rm -rf "$BACKUP_NAME"
    else
        log_error "Ошибка создания архива"
        exit 1
    fi
}

# Очистка старых бэкапов
cleanup_old_backups() {
    log_info "Очистка старых бэкапов..."
    
    # Удаление бэкапов старше 30 дней
    find "$BACKUP_DIR" -name "jarvis_backup_*.tar.gz" -mtime +30 -delete 2>/dev/null || true
    
    log_success "Старые бэкапы очищены"
}

# Создание информации о бэкапе
create_backup_info() {
    log_info "Создание информации о бэкапе..."
    
    cat > "$BACKUP_PATH/backup_info.txt" << EOF
Jarvis AI Assistant - Информация о бэкапе
==========================================

Дата создания: $(date)
Версия: 1.0.0
Размер: $(du -sh "$BACKUP_PATH" 2>/dev/null | cut -f1)

Содержимое:
- database.sql - Бэкап базы данных PostgreSQL
- configs/ - Конфигурационные файлы
- logs/ - Логи системы
- models/ - Модели ИИ
- learning/ - Данные обучения

Восстановление:
1. Распаковать архив: tar -xzf ${BACKUP_NAME}.tar.gz
2. Восстановить БД: docker-compose exec -T postgres psql -U jarvis -d jarvis_db < database.sql
3. Скопировать конфиги: cp -r configs/* shared/config/
4. Перезапустить сервисы: docker-compose restart

EOF
    
    log_success "Информация о бэкапе создана"
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Backup Script"
    echo "=========================================="
    echo
    
    create_backup_dir
    backup_database
    backup_configs
    backup_logs
    backup_models
    backup_learning_data
    create_backup_info
    create_archive
    cleanup_old_backups
    
    echo
    echo "=========================================="
    echo "  Бэкап завершен!"
    echo "=========================================="
    echo
    echo "Архив: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    echo "Размер: $(du -sh "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" 2>/dev/null | cut -f1)"
    echo
    echo "Для восстановления используйте:"
    echo "  ./scripts/restore.sh $BACKUP_NAME"
    echo
}

# Запуск основной функции
main "$@"