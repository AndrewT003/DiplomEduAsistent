# 🐳 Docker Deployment Guide

Інструкція по запуску проекту через Docker.

## 📋 Передумови

- Docker Desktop встановлено і запущено
- Docker Compose v2.0+

## 🚀 Швидкий старт

### 1. Налаштування змінних оточення

Скопіюйте `.env.example` в `.env` і заповніть своїми ключами:

```bash
# В кореневій директорії
cp .env.example .env

# В backend директорії
cp backend/.env.example backend/.env
```

Відредагуйте `backend/.env` і додайте свої credentials:
- Supabase URL і ключі
- Groq API key
- Qdrant URL і API key

### 2. Запуск контейнерів

```bash
# Зібрати і запустити всі сервіси
docker-compose up --build

# Або в фоновому режимі
docker-compose up -d --build
```

### 3. Доступ до додатку

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🛠️ Корисні команди

```bash
# Зупинити всі контейнери
docker-compose down

# Зупинити і видалити volumes
docker-compose down -v

# Переглянути логи
docker-compose logs -f

# Переглянути логи конкретного сервісу
docker-compose logs -f backend
docker-compose logs -f frontend

# Перезапустити сервіс
docker-compose restart backend
docker-compose restart frontend

# Зайти в контейнер
docker-compose exec backend bash
docker-compose exec frontend sh

# Перебудувати конкретний сервіс
docker-compose up -d --build backend
```

## 📁 Структура

```
coursework_1/
├── backend/
│   ├── Dockerfile          # Backend Docker image
│   ├── .dockerignore       # Файли які ігноруються при build
│   ├── requirements.txt    # Python залежності
│   └── ...
├── frontend/
│   ├── Dockerfile          # Frontend Docker image (multi-stage)
│   ├── nginx.conf          # Nginx конфігурація
│   ├── .dockerignore       # Файли які ігноруються при build
│   └── ...
├── docker-compose.yml      # Docker Compose конфігурація
└── .env                    # Змінні оточення (не в git!)
```

## 🔧 Development vs Production

### Development режим

Для development можна використати volume mounting щоб зміни коду відразу відображалися:

```yaml
# В docker-compose.yml розкоментуйте:
volumes:
  - ./backend:/app
```

Або запустіть тільки залежності (БД) в Docker, а backend/frontend локально.

### Production режим

В production frontend будується як статичні файли і сервується через nginx.
Backend запускається з uvicorn.

## 🐛 Troubleshooting

### Порти зайняті

Якщо порти 80 або 8000 зайняті, змініть їх в `docker-compose.yml`:

```yaml
ports:
  - "3000:80"    # замість 80:80
  - "8001:8000"  # замість 8000:8000
```

### Проблеми з .env файлами

Переконайтеся що:
1. `.env` файл існує в кореневій директорії
2. `backend/.env` файл існує і містить всі необхідні ключі
3. Немає пробілів навколо `=` в .env файлах

### Frontend не може з'єднатися з backend

Перевірте:
1. Backend контейнер запущений: `docker-compose ps`
2. Backend логи: `docker-compose logs backend`
3. Nginx конфігурація в `frontend/nginx.conf` правильна

### База даних недоступна

Перевірте що:
1. Supabase credentials правильні
2. Ваш IP не заблокований в Supabase
3. Qdrant доступний за вказаним URL

## 📊 Моніторинг

Переглянути статус контейнерів:

```bash
docker-compose ps
```

Переглянути використання ресурсів:

```bash
docker stats
```

## 🔒 Безпека

**ВАЖЛИВО**: Ніколи не коммітьте `.env` файли в git!

`.env` файли вже додані в `.gitignore`.

## 📝 Оновлення

Після змін в коді:

```bash
# Перебудувати і перезапустити
docker-compose up -d --build

# Або тільки конкретний сервіс
docker-compose up -d --build backend
```

## 🎉 Готово!

Ваш проект запущений в Docker і готовий до використання!
