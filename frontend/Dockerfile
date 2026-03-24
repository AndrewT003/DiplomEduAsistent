# Frontend Dockerfile (Production build)
FROM node:18-alpine AS build

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо package файли
COPY package*.json ./

# Встановлюємо залежності
RUN npm ci

# Копіюємо всі файли
COPY . .

# Будуємо production build
RUN npm run build

# Production stage - nginx
FROM nginx:alpine

# Копіюємо build файли в nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Копіюємо nginx конфігурацію
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Відкриваємо порт
EXPOSE 80

# Запускаємо nginx
CMD ["nginx", "-g", "daemon off;"]
