FROM node:18-alpine

# Установка системных зависимостей
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git

# Создание директории приложения
WORKDIR /app

# Копирование package.json и package-lock.json
COPY package*.json ./

# Установка зависимостей
RUN npm ci --only=production

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN npm run build

# Установка serve для раздачи статических файлов
RUN npm install -g serve

# Открытие порта
EXPOSE 3000

# Запуск приложения
CMD ["serve", "-s", "build", "-l", "3000"]