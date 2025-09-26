#!/bin/bash

# Скрипт настройки Jarvis для внешнего IP
# Автор: Jarvis AI Assistant
# Версия: 1.0.0

set -e

EXTERNAL_IP="194.247.186.190"
LOCAL_IP="0.0.0.0"

echo "🌐 Настройка Jarvis для внешнего IP: $EXTERNAL_IP"
echo "=================================================="

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    exit 1
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi

echo "✅ Docker и Docker Compose найдены"

# Остановка существующих сервисов
echo "🛑 Остановка существующих сервисов..."
export DOCKER_HOST=tcp://localhost:2375
docker-compose -f docker-compose.simple.yml down 2>/dev/null || true
docker-compose -f docker-compose.external.yml down 2>/dev/null || true

# Запуск сервисов с внешней конфигурацией
echo "🚀 Запуск сервисов с внешней конфигурацией..."
docker-compose -f docker-compose.external.yml up -d

# Ожидание запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверка статуса сервисов
echo "📊 Проверка статуса сервисов..."
docker-compose -f docker-compose.external.yml ps

# Проверка доступности API
echo "🔍 Проверка доступности API..."
sleep 5

# Проверка локального доступа
echo "   Локальный доступ:"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ http://localhost:8000 - доступен"
else
    echo "   ❌ http://localhost:8000 - недоступен"
fi

# Проверка внешнего доступа (если IP доступен)
echo "   Внешний доступ:"
if curl -s --connect-timeout 5 http://$EXTERNAL_IP:8000/health > /dev/null; then
    echo "   ✅ http://$EXTERNAL_IP:8000 - доступен"
else
    echo "   ⚠️  http://$EXTERNAL_IP:8000 - недоступен (возможно, нужно настроить файрвол)"
fi

echo ""
echo "🎉 Настройка завершена!"
echo ""
echo "🌐 Доступные интерфейсы:"
echo "   • Локальный веб-интерфейс: http://localhost:8000"
echo "   • Внешний веб-интерфейс: http://$EXTERNAL_IP:8000"
echo "   • API документация: http://$EXTERNAL_IP:8000/docs"
echo "   • Health Check: http://$EXTERNAL_IP:8000/health"
echo ""
echo "🔧 Управление сервисами:"
echo "   • Статус: docker-compose -f docker-compose.external.yml ps"
echo "   • Логи: docker-compose -f docker-compose.external.yml logs -f"
echo "   • Остановка: docker-compose -f docker-compose.external.yml down"
echo "   • Перезапуск: docker-compose -f docker-compose.external.yml restart"
echo ""
echo "🧪 Тестирование:"
echo "   • Автоматический тест: python3 demo.py"
echo "   • Ручное тестирование: curl http://$EXTERNAL_IP:8000/health"
echo ""
echo "⚠️  Важно:"
echo "   • Убедитесь, что порты 80, 443, 8000 открыты в файрволе"
echo "   • Для HTTPS настройте SSL сертификаты"
echo "   • Проверьте настройки роутера/прокси"