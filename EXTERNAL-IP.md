# 🌐 Jarvis AI Assistant - Внешний IP

## ✅ Настройка завершена

**Jarvis AI Assistant настроен для работы с внешним IP: 194.247.186.190** 🚀

### 🏃‍♂️ Запущенные сервисы

- ✅ **PostgreSQL** - База данных (порт 5432)
- ✅ **Redis** - Очереди сообщений (порт 6379)  
- ✅ **Simple API** - Основной API сервис (порт 8000)

### 🌐 Доступные интерфейсы

#### Локальный доступ
- **Веб-интерфейс**: http://localhost:8000
- **API документация**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

#### Внешний доступ
- **Веб-интерфейс**: http://194.247.186.190:8000
- **API документация**: http://194.247.186.190:8000/docs
- **Health Check**: http://194.247.186.190:8000/health

## 🧪 Тестирование

### Локальное тестирование
```bash
python3 demo-local.py
```

### Внешнее тестирование
```bash
# Проверка здоровья
curl http://194.247.186.190:8000/health

# Отправка сообщения
curl -X POST http://194.247.186.190:8000/message \
  -H "Content-Type: application/json" \
  -d '{"text": "Привет, Jarvis!", "user_id": "test_user"}'

# Получение статуса
curl http://194.247.186.190:8000/status
```

## 🔧 Управление сервисами

### Просмотр статуса
```bash
export DOCKER_HOST=tcp://localhost:2375
docker-compose -f docker-compose.external.yml ps
```

### Просмотр логов
```bash
docker-compose -f docker-compose.external.yml logs -f simple-api
```

### Остановка сервисов
```bash
docker-compose -f docker-compose.external.yml down
```

### Перезапуск
```bash
docker-compose -f docker-compose.external.yml restart simple-api
```

## 🔒 Настройка безопасности

### Файрвол
Убедитесь, что порт 8000 открыт в файрволе:

```bash
# Ubuntu/Debian
sudo ufw allow 8000

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### SSL/HTTPS
Для настройки HTTPS:

1. Получите SSL сертификат (Let's Encrypt)
2. Обновите nginx конфигурацию
3. Перезапустите сервисы

### Аутентификация
Для добавления аутентификации:

1. Обновите API Gateway
2. Настройте JWT токены
3. Добавьте middleware для проверки

## 📊 Мониторинг

### Проверка доступности
```bash
# Локальная проверка
curl -s http://localhost:8000/health

# Внешняя проверка
curl -s http://194.247.186.190:8000/health
```

### Мониторинг логов
```bash
# Логи API
docker-compose -f docker-compose.external.yml logs -f simple-api

# Логи базы данных
docker-compose -f docker-compose.external.yml logs -f postgres

# Логи Redis
docker-compose -f docker-compose.external.yml logs -f redis
```

## 🚀 Масштабирование

### Горизонтальное масштабирование
```bash
# Увеличение количества API сервисов
docker-compose -f docker-compose.external.yml up -d --scale simple-api=3
```

### Load Balancer
Для распределения нагрузки:

1. Настройте nginx как load balancer
2. Добавьте health checks
3. Настройте failover

## 🔧 Конфигурация

### Переменные окружения
```bash
# В docker-compose.external.yml
environment:
  - HOST=0.0.0.0
  - PORT=8000
  - REDIS_URL=redis://redis:6379
  - POSTGRES_URL=postgresql://jarvis:jarvis_password@postgres:5432/jarvis
```

### Настройка базы данных
```bash
# Подключение к PostgreSQL
docker exec -it jarvis_postgres_1 psql -U jarvis -d jarvis
```

### Настройка Redis
```bash
# Подключение к Redis
docker exec -it jarvis_redis_1 redis-cli
```

## 📈 Производительность

### Оптимизация
- Используйте connection pooling
- Настройте кэширование
- Оптимизируйте запросы к БД

### Мониторинг
- Настройте Prometheus
- Добавьте Grafana дашборды
- Мониторьте метрики

## 🆘 Устранение неполадок

### Проблемы с подключением
```bash
# Проверка портов
netstat -tlnp | grep 8000

# Проверка Docker
docker ps | grep jarvis

# Проверка логов
docker-compose -f docker-compose.external.yml logs
```

### Проблемы с производительностью
```bash
# Мониторинг ресурсов
docker stats

# Проверка использования диска
df -h

# Проверка памяти
free -h
```

## 📚 Дополнительные ресурсы

- **Полная документация**: README.md
- **Демонстрация**: DEMO.md
- **Скрипты управления**: scripts/
- **Kubernetes манифесты**: k8s/

---

**Jarvis AI Assistant готов к работе с внешним IP!** 🤖✨

*IP: 194.247.186.190:8000*