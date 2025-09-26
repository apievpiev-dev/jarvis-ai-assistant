# Скрипты управления Jarvis AI Assistant

Этот каталог содержит скрипты для управления и мониторинга Jarvis AI Assistant.

## Основные скрипты

### Установка и настройка

- **`install-dependencies.sh`** - Установка всех необходимых зависимостей
- **`setup.sh`** - Первоначальная настройка системы
- **`quick-start.sh`** - Быстрый запуск Jarvis AI Assistant

### Управление сервисами

- **`start.sh`** - Запуск всех сервисов
- **`stop.sh`** - Остановка всех сервисов
- **`restart.sh`** - Перезапуск всех сервисов
- **`status.sh`** - Проверка статуса системы

### Мониторинг и обслуживание

- **`health-check.sh`** - Проверка здоровья системы
- **`monitor.sh`** - Мониторинг системы в реальном времени
- **`backup.sh`** - Создание резервных копий
- **`restore.sh`** - Восстановление из резервной копии
- **`update.sh`** - Обновление системы
- **`cleanup.sh`** - Очистка системы

### Развертывание

- **`deploy-k8s.sh`** - Развертывание в Kubernetes
- **`download_models.py`** - Загрузка моделей ИИ

### Интеграции

- **`telegram-bot.sh`** - Управление через Telegram

## Использование

### Первоначальная установка

```bash
# Установка зависимостей
./scripts/install-dependencies.sh

# Настройка системы
./scripts/setup.sh

# Быстрый запуск
./scripts/quick-start.sh
```

### Ежедневное управление

```bash
# Проверка статуса
./scripts/status.sh

# Проверка здоровья
./scripts/health-check.sh

# Просмотр логов
./scripts/logs.sh

# Перезапуск сервисов
./scripts/restart.sh
```

### Обслуживание

```bash
# Создание бэкапа
./scripts/backup.sh

# Восстановление из бэкапа
./scripts/restore.sh <backup_name>

# Обновление системы
./scripts/update.sh

# Очистка системы
./scripts/cleanup.sh
```

### Развертывание в Kubernetes

```bash
# Развертывание в Kubernetes
./scripts/deploy-k8s.sh

# Масштабирование
./scripts/scale.sh <deployment> <replicas>

# Обновление
./scripts/k8s-update.sh

# Удаление
./scripts/k8s-delete.sh
```

### Управление через Telegram

```bash
# Запуск Telegram бота
./scripts/telegram-bot.sh
```

## Конфигурация

### Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Основные переменные:

- `TELEGRAM_BOT_TOKEN` - Токен Telegram бота
- `TELEGRAM_CHAT_ID` - ID чата для уведомлений
- `POSTGRES_PASSWORD` - Пароль PostgreSQL
- `REDIS_PASSWORD` - Пароль Redis

### Настройка мониторинга

Скрипты автоматически настраивают:

- Prometheus для сбора метрик
- Grafana для визуализации
- Логирование в `/workspace/jarvis/logs/`
- Cron задачи для автоматического обслуживания

## Логирование

Все скрипты записывают логи в `/workspace/jarvis/logs/`:

- `install_dependencies.log` - Лог установки зависимостей
- `setup.log` - Лог настройки системы
- `quick_start.log` - Лог быстрого запуска
- `status.log` - Лог проверки статуса
- `health_check.log` - Лог проверки здоровья
- `monitor.log` - Лог мониторинга
- `backup.log` - Лог создания бэкапов
- `restore.log` - Лог восстановления
- `update.log` - Лог обновлений
- `cleanup.log` - Лог очистки
- `telegram_bot.log` - Лог Telegram бота

## Автоматизация

Скрипты автоматически настраивают cron задачи:

- Ежедневный бэкап в 2:00
- Ежедневная очистка в 3:00
- Проверка здоровья каждые 5 минут
- Еженедельное обновление в воскресенье в 1:00

## Безопасность

Скрипты автоматически настраивают:

- UFW файрвол с минимальными портами
- fail2ban для защиты от атак
- Автоматическое логирование
- Резервное копирование

## Устранение неполадок

### Проверка статуса

```bash
# Общий статус
./scripts/status.sh

# Детальная проверка здоровья
./scripts/health-check.sh

# Просмотр логов
./scripts/logs.sh
```

### Восстановление

```bash
# Автоматическое восстановление
./scripts/health-check.sh

# Восстановление из бэкапа
./scripts/restore.sh <backup_name>

# Перезапуск сервисов
./scripts/restart.sh
```

### Очистка

```bash
# Очистка системы
./scripts/cleanup.sh

# Очистка Docker
docker system prune -f
```

## Поддержка

При возникновении проблем:

1. Проверьте логи в `/workspace/jarvis/logs/`
2. Запустите `./scripts/status.sh` для диагностики
3. Используйте `./scripts/health-check.sh` для автоматического восстановления
4. При необходимости восстановите из бэкапа

## Лицензия

Все скрипты распространяются под лицензией MIT.