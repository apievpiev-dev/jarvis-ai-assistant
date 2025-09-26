#!/bin/bash

# Скрипт управления Jarvis AI Assistant через Telegram
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
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"
LOG_FILE="/workspace/jarvis/logs/telegram_bot.log"

# Создание директории для логов
mkdir -p /workspace/jarvis/logs

# Функция для записи в лог
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Функция для отправки сообщения в Telegram
send_telegram_message() {
    local message="$1"
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
        log_warning "Telegram не настроен, пропускаем отправку сообщения"
        return
    fi
    
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d chat_id="$TELEGRAM_CHAT_ID" \
        -d text="$message" \
        -d parse_mode="HTML" > /dev/null
    
    if [ $? -eq 0 ]; then
        log_success "Сообщение отправлено в Telegram"
        log_to_file "SUCCESS: Сообщение отправлено в Telegram: $message"
    else
        log_error "Ошибка отправки сообщения в Telegram"
        log_to_file "ERROR: Ошибка отправки сообщения в Telegram"
    fi
}

# Функция для получения обновлений от Telegram
get_telegram_updates() {
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        return
    fi
    
    local updates=$(curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates")
    echo "$updates"
}

# Функция для обработки команд Telegram
process_telegram_command() {
    local command="$1"
    local chat_id="$2"
    
    case "$command" in
        "/start")
            send_telegram_message "🤖 <b>Jarvis AI Assistant</b> запущен и готов к работе!"
            ;;
        "/status")
            local status=$(docker-compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || echo "Сервисы недоступны")
            send_telegram_message "📊 <b>Статус системы:</b>\n<pre>$status</pre>"
            ;;
        "/health")
            local health=$(./scripts/health-check.sh 2>&1 | tail -10)
            send_telegram_message "🏥 <b>Проверка здоровья:</b>\n<pre>$health</pre>"
            ;;
        "/logs")
            local logs=$(docker-compose logs --tail=20 2>&1 | tail -10)
            send_telegram_message "📝 <b>Последние логи:</b>\n<pre>$logs</pre>"
            ;;
        "/restart")
            send_telegram_message "🔄 Перезапуск сервисов..."
            docker-compose restart
            sleep 10
            send_telegram_message "✅ Сервисы перезапущены"
            ;;
        "/update")
            send_telegram_message "⬆️ Начинаю обновление системы..."
            ./scripts/update.sh
            send_telegram_message "✅ Обновление завершено"
            ;;
        "/backup")
            send_telegram_message "💾 Создание бэкапа..."
            ./scripts/backup.sh
            send_telegram_message "✅ Бэкап создан"
            ;;
        "/cleanup")
            send_telegram_message "🧹 Очистка системы..."
            ./scripts/cleanup.sh
            send_telegram_message "✅ Очистка завершена"
            ;;
        "/help")
            local help_text="🤖 <b>Доступные команды:</b>\n\n"
            help_text+="/start - Запуск бота\n"
            help_text+="/status - Статус системы\n"
            help_text+="/health - Проверка здоровья\n"
            help_text+="/logs - Последние логи\n"
            help_text+="/restart - Перезапуск сервисов\n"
            help_text+="/update - Обновление системы\n"
            help_text+="/backup - Создание бэкапа\n"
            help_text+="/cleanup - Очистка системы\n"
            help_text+="/help - Справка"
            send_telegram_message "$help_text"
            ;;
        *)
            send_telegram_message "❓ Неизвестная команда. Используйте /help для получения справки."
            ;;
    esac
}

# Функция для мониторинга системы и отправки уведомлений
monitor_system() {
    log_info "Запуск мониторинга системы..."
    
    while true; do
        # Проверка доступности API Gateway
        if ! curl -s --max-time 5 "http://localhost:8000/health" > /dev/null; then
            send_telegram_message "🚨 <b>ВНИМАНИЕ!</b> API Gateway недоступен!"
            log_to_file "WARNING: API Gateway недоступен, отправлено уведомление"
        fi
        
        # Проверка использования диска
        disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
        if [ "$disk_usage" -gt 90 ]; then
            send_telegram_message "💾 <b>ВНИМАНИЕ!</b> Критически мало свободного места: ${disk_usage}%"
            log_to_file "WARNING: Критически мало свободного места: ${disk_usage}%"
        fi
        
        # Проверка использования памяти
        memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
        if [ "$memory_usage" -gt 90 ]; then
            send_telegram_message "🧠 <b>ВНИМАНИЕ!</b> Высокое использование памяти: ${memory_usage}%"
            log_to_file "WARNING: Высокое использование памяти: ${memory_usage}%"
        fi
        
        # Ожидание перед следующей проверкой
        sleep 300  # 5 минут
    done
}

# Функция для обработки входящих сообщений
process_messages() {
    log_info "Запуск обработки сообщений..."
    
    while true; do
        # Получение обновлений
        updates=$(get_telegram_updates)
        
        if [ -n "$updates" ]; then
            # Обработка каждого обновления
            echo "$updates" | jq -r '.result[] | select(.message.text) | "\(.message.chat.id) \(.message.text)"' 2>/dev/null | while read chat_id command; do
                if [ -n "$chat_id" ] && [ -n "$command" ]; then
                    log_info "Получена команда: $command от чата: $chat_id"
                    process_telegram_command "$command" "$chat_id"
                fi
            done
        fi
        
        # Ожидание перед следующей проверкой
        sleep 5
    done
}

# Функция для настройки Telegram
setup_telegram() {
    log_info "Настройка Telegram..."
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        log_error "TELEGRAM_BOT_TOKEN не установлен"
        log_info "Установите переменную окружения TELEGRAM_BOT_TOKEN"
        exit 1
    fi
    
    if [ -z "$TELEGRAM_CHAT_ID" ]; then
        log_error "TELEGRAM_CHAT_ID не установлен"
        log_info "Установите переменную окружения TELEGRAM_CHAT_ID"
        exit 1
    fi
    
    # Проверка токена
    local bot_info=$(curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe")
    if echo "$bot_info" | grep -q '"ok":true'; then
        log_success "Telegram бот настроен успешно"
        log_to_file "SUCCESS: Telegram бот настроен успешно"
    else
        log_error "Ошибка настройки Telegram бота"
        log_to_file "ERROR: Ошибка настройки Telegram бота"
        exit 1
    fi
}

# Основная функция
main() {
    echo "=========================================="
    echo "  Jarvis AI Assistant - Telegram Bot"
    echo "=========================================="
    echo
    
    log_to_file "INFO: Запуск Telegram бота"
    
    setup_telegram
    
    # Отправка уведомления о запуске
    send_telegram_message "🚀 <b>Jarvis AI Assistant</b> запущен и готов к работе!"
    
    # Запуск мониторинга в фоне
    monitor_system &
    MONITOR_PID=$!
    
    # Запуск обработки сообщений в фоне
    process_messages &
    MESSAGES_PID=$!
    
    log_success "Telegram бот запущен"
    log_info "PID мониторинга: $MONITOR_PID"
    log_info "PID обработки сообщений: $MESSAGES_PID"
    
    # Ожидание завершения
    wait $MONITOR_PID $MESSAGES_PID
}

# Обработка сигналов
trap 'log_info "Получен сигнал завершения, останавливаю бота..."; kill $MONITOR_PID $MESSAGES_PID 2>/dev/null; exit 0' SIGINT SIGTERM

# Запуск основной функции
main "$@"