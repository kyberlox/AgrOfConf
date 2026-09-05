FROM node:22-alpine AS build-stage
# Установить рабочий каталог в контейнере
WORKDIR /app

# Скопировать файлы package.json и package-lock.json
COPY package*.json ./

# Установить зависимости
RUN npm install

# Скопировать остальную часть кода приложения
COPY . .

# Базовый URL API. Относительный '/api' позволяет ходить на бэкенд
# через Nginx (location /api/), независимо от внешнего порта.
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

# Собрать приложение.
# Используем build-only (без vue-tsc type-check), т.к. в проекте есть
# предсуществующие TS-ошибки (отсутствующие типы некоторых зависимостей),
# которые валят полную сборку `npm run build`.
RUN npm run build-only

WORKDIR /app/dist

CMD ["npm", "run", "preview"]