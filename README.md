# 🤖 Jarvis AI Assistant

Полнофункциональный AI-ассистент с микросервисной архитектурой, голосовым интерфейсом, самообучением и горизонтальным масштабированием.

## 🚀 Возможности

### 🎤 Голосовой интерфейс
- **Распознавание речи** (Whisper) на русском языке
- **Синтез речи** высокого качества
- **Реальное время** обработки аудио
- **WebSocket** соединения для низкой задержки

### 🧠 Искусственный интеллект
- **Phi-2** модель для обработки команд
- **Естественное понимание** языка
- **Контекстное** планирование задач
- **CPU-оптимизированные** модели

### ⚙️ Выполнение задач
- **Файловые операции** (создание, редактирование, удаление)
- **Управление браузером** (открытие страниц, поиск)
- **Системные команды** (запуск программ, управление процессами)
- **Операции с кодом** (анализ, модификация, рефакторинг)
- **Система напоминаний** и планировщик

### 📊 Анализ и модификация кода
- **Синтаксический анализ** (Python, JavaScript, TypeScript, Java, C++, C)
- **Проверка качества** кода
- **Анализ безопасности** и производительности
- **Автоматический рефакторинг**
- **Генерация тестов**
- **Предложения улучшений**

### 🎓 Самообучение
- **Обучение с учителем** и без учителя
- **Обучение с подкреплением**
- **Трансферное обучение**
- **База знаний** с поиском
- **Адаптация** к пользователю
- **Обратная связь** и оптимизация

### 🌐 Веб-интерфейс
- **Современный React** интерфейс
- **WebSocket** для реального времени
- **Голосовое управление**
- **Чат-интерфейс**
- **Мониторинг** системы

### 🔧 Архитектура
- **Микросервисы** с Docker
- **API Gateway** с балансировкой нагрузки
- **PostgreSQL** для данных
- **Redis** для очередей
- **Kubernetes** для оркестрации
- **Prometheus + Grafana** для мониторинга

## 📁 Структура проекта

```
jarvis/
├── services/                    # Микросервисы
│   ├── voice-service/          # Голосовой интерфейс
│   ├── brain-service/          # AI обработка
│   ├── task-service/           # Выполнение задач
│   ├── web-service/            # Веб-интерфейс
│   ├── code-service/           # Анализ кода
│   ├── learning-service/       # Самообучение
│   └── api-gateway/            # API Gateway
├── shared/                     # Общие ресурсы
│   ├── models/                 # AI модели
│   ├── config/                 # Конфигурации
│   ├── utils/                  # Утилиты
│   └── memory/                 # Данные обучения
├── k8s/                        # Kubernetes манифесты
├── scripts/                    # Скрипты управления
├── docker-compose.yml          # Docker Compose
└── README.md                   # Документация
```

## 🚀 Быстрый старт

### 1. Клонирование и настройка

```bash
git clone <repository-url>
cd jarvis

# Установка зависимостей
./scripts/install-dependencies.sh

# Настройка системы
./scripts/setup.sh
```

### 2. Запуск

```bash
# Быстрый запуск
./scripts/quick-start.sh

# Или полный запуск
./scripts/start.sh
```

### 3. Доступ к сервисам

- **Веб-интерфейс**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090

## 🐳 Docker

### Запуск с Docker Compose

```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### Управление сервисами

```bash
# Перезапуск
./scripts/restart.sh

# Остановка
./scripts/stop.sh

# Статус
./scripts/status.sh

# Логи
./scripts/logs.sh
```

## ☸️ Kubernetes

### Развертывание в Kubernetes

```bash
# Развертывание
./scripts/deploy-k8s.sh

# Масштабирование
./scripts/scale.sh api-gateway 3

# Обновление
./scripts/k8s-update.sh

# Удаление
./scripts/k8s-delete.sh
```

### Мониторинг

```bash
# Проверка статуса
kubectl get pods -n jarvis

# Логи
./scripts/k8s-logs.sh

# Масштабирование
kubectl scale deployment api-gateway --replicas=5 -n jarvis
```

## 🔧 Конфигурация

### Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Основные переменные:

```env
# База данных
POSTGRES_PASSWORD=your_password
REDIS_PASSWORD=your_redis_password

# Telegram (опционально)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Модели ИИ
MODEL_PATH=/app/models
```

### Настройка сервисов

Каждый сервис имеет свою конфигурацию в `shared/config/`:

- **PostgreSQL**: `shared/config/postgres/init.sql`
- **Prometheus**: `shared/config/prometheus/prometheus.yml`
- **Grafana**: `shared/config/grafana/`

## 📊 Мониторинг

### Prometheus метрики

- **Производительность**: CPU, память, диск
- **Сетевые**: трафик, задержки
- **Бизнес**: количество запросов, ошибки
- **Кастомные**: метрики приложений

### Grafana дашборды

- **Обзор системы**: общее состояние
- **Производительность**: детальные метрики
- **Бизнес-метрики**: использование функций
- **Алерты**: уведомления о проблемах

## 🔒 Безопасность

### Встроенные меры

- **UFW файрвол** с минимальными портами
- **fail2ban** для защиты от атак
- **Авторизация** через API ключи
- **Шифрование** данных в покое
- **Логирование** всех операций

### Рекомендации

1. **Измените пароли** по умолчанию
2. **Настройте SSL/TLS** для продакшена
3. **Ограничьте доступ** к API
4. **Регулярно обновляйте** зависимости
5. **Мониторьте** логи на подозрительную активность

## 🎯 Использование

### Голосовые команды

```
"Привет, Jarvis" - Активация
"Открой браузер" - Управление браузером
"Создай файл test.txt" - Файловые операции
"Напомни мне в 15:00" - Напоминания
"Проанализируй код" - Анализ кода
"Остановись" - Деактивация
```

### API команды

```bash
# Анализ кода
curl -X POST http://localhost:8006/ws \
  -H "Content-Type: application/json" \
  -d '{
    "type": "analyze",
    "data": {
      "code": "def hello(): print(\"Hello\")",
      "language": "python"
    }
  }'

# Обучение
curl -X POST http://localhost:8007/ws \
  -H "Content-Type: application/json" \
  -d '{
    "type": "learn",
    "data": {
      "input": "пользовательский ввод",
      "output": "ожидаемый ответ"
    }
  }'
```

## 🔄 Обслуживание

### Автоматические задачи

- **Ежедневный бэкап** в 2:00
- **Ежедневная очистка** в 3:00
- **Проверка здоровья** каждые 5 минут
- **Еженедельное обновление** в воскресенье

### Ручное обслуживание

```bash
# Создание бэкапа
./scripts/backup.sh

# Восстановление
./scripts/restore.sh backup_name

# Обновление
./scripts/update.sh

# Очистка
./scripts/cleanup.sh
```

## 📱 Telegram бот

### Настройка

1. Создайте бота через @BotFather
2. Получите токен и ID чата
3. Добавьте в `.env` файл
4. Запустите бота: `./scripts/telegram-bot.sh`

### Команды

```
/start - Запуск бота
/status - Статус системы
/health - Проверка здоровья
/logs - Последние логи
/restart - Перезапуск сервисов
/update - Обновление системы
/backup - Создание бэкапа
/cleanup - Очистка системы
/help - Справка
```

## 🐛 Устранение неполадок

### Проверка статуса

```bash
# Общий статус
./scripts/status.sh

# Детальная проверка
./scripts/health-check.sh

# Логи
./scripts/logs.sh
```

### Частые проблемы

1. **Сервисы не запускаются**
   - Проверьте Docker: `docker ps`
   - Проверьте логи: `./scripts/logs.sh`
   - Проверьте порты: `netstat -tlnp`

2. **Высокое использование ресурсов**
   - Запустите очистку: `./scripts/cleanup.sh`
   - Проверьте мониторинг: http://localhost:3001
   - Масштабируйте сервисы: `./scripts/scale.sh`

3. **Проблемы с базой данных**
   - Проверьте подключение: `docker-compose exec postgres psql -U jarvis -d jarvis`
   - Восстановите из бэкапа: `./scripts/restore.sh`

## 📈 Масштабирование

### Горизонтальное масштабирование

```bash
# Docker Compose
docker-compose up -d --scale api-gateway=3

# Kubernetes
kubectl scale deployment api-gateway --replicas=5 -n jarvis
```

### Автоматическое масштабирование

```bash
# Настройка HPA
kubectl autoscale deployment api-gateway --cpu-percent=70 --min=2 --max=10 -n jarvis
```

## 🤝 Разработка

### Добавление нового сервиса

1. Создайте директорию в `services/`
2. Добавьте `Dockerfile` и `requirements.txt`
3. Создайте `main.py` с FastAPI
4. Добавьте в `docker-compose.yml`
5. Создайте Kubernetes манифесты
6. Обновите API Gateway

### Тестирование

```bash
# Запуск тестов
python -m pytest tests/

# Проверка качества кода
./scripts/code-analysis.sh

# Тестирование API
./scripts/api-tests.sh
```

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🙏 Благодарности

- **OpenAI** за Whisper модель
- **Microsoft** за Phi-2 модель
- **FastAPI** за отличный фреймворк
- **React** за современный UI
- **Docker** за контейнеризацию
- **Kubernetes** за оркестрацию

## 📞 Поддержка

- **Документация**: [Wiki](wiki-url)
- **Issues**: [GitHub Issues](issues-url)
- **Discussions**: [GitHub Discussions](discussions-url)
- **Telegram**: [@jarvis_support](telegram-url)

---

**Jarvis AI Assistant** - Ваш умный помощник для работы и развлечений! 🤖✨