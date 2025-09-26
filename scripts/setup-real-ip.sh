#!/bin/bash

# Скрипт настройки Jarvis для реальных IP адресов
# Автор: Jarvis AI Assistant
# Версия: 1.0.0

set -e

echo "🌐 Настройка Jarvis для реальных IP адресов"
echo "============================================="

# Получение реальных IP адресов
REAL_IPS=$(hostname -I)
echo "📍 Найденные IP адреса: $REAL_IPS"

# Выбор основного IP
MAIN_IP=$(echo $REAL_IPS | awk '{print $1}')
echo "🎯 Основной IP: $MAIN_IP"

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
docker-compose -f docker-compose.real-ip.yml down 2>/dev/null || true

# Запуск сервисов с реальными IP
echo "🚀 Запуск сервисов с реальными IP..."
docker-compose -f docker-compose.real-ip.yml up -d

# Ожидание запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверка статуса сервисов
echo "📊 Проверка статуса сервисов..."
docker-compose -f docker-compose.real-ip.yml ps

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

# Проверка доступа по основному IP
echo "   Доступ по основному IP:"
if curl -s --connect-timeout 5 http://$MAIN_IP:8000/health > /dev/null; then
    echo "   ✅ http://$MAIN_IP:8000 - доступен"
else
    echo "   ❌ http://$MAIN_IP:8000 - недоступен"
fi

# Проверка всех IP адресов
echo "   Проверка всех IP адресов:"
for ip in $REAL_IPS; do
    if curl -s --connect-timeout 3 http://$ip:8000/health > /dev/null; then
        echo "   ✅ http://$ip:8000 - доступен"
    else
        echo "   ❌ http://$ip:8000 - недоступен"
    fi
done

echo ""
echo "🎉 Настройка завершена!"
echo ""
echo "🌐 Доступные интерфейсы:"
echo "   • Локальный веб-интерфейс: http://localhost:8000"
for ip in $REAL_IPS; do
    echo "   • Веб-интерфейс по IP $ip: http://$ip:8000"
done
echo "   • API документация: http://$MAIN_IP:8000/docs"
echo "   • Health Check: http://$MAIN_IP:8000/health"
echo ""
echo "🔧 Управление сервисами:"
echo "   • Статус: docker-compose -f docker-compose.real-ip.yml ps"
echo "   • Логи: docker-compose -f docker-compose.real-ip.yml logs -f"
echo "   • Остановка: docker-compose -f docker-compose.real-ip.yml down"
echo "   • Перезапуск: docker-compose -f docker-compose.real-ip.yml restart"
echo ""
echo "🧪 Тестирование:"
echo "   • Локальный тест: python3 demo-local.py"
echo "   • Тест по IP: curl http://$MAIN_IP:8000/health"
echo ""
echo "⚠️  Важно:"
echo "   • Используйте реальные IP адреса для доступа"
echo "   • Убедитесь, что порты 8000, 5432, 6379 открыты в файрволе"
echo "   • Для внешнего доступа настройте роутер/прокси"