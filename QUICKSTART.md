# 🚀 Quick Start Guide

## Запуск за 3 кроки:

### 1️⃣ Налаштуйте змінні оточення

```bash
# Windows (PowerShell або CMD)
copy .env.example .env
copy backend\.env.example backend\.env

# Linux/Mac
cp .env.example .env
cp backend/.env.example backend/.env
```

Відредагуйте `backend/.env` і додайте свої ключі:
- Supabase credentials
- Groq API key
- Qdrant credentials

### 2️⃣ Запустіть проект

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

**Або вручну:**
```bash
docker-compose up --build
```

### 3️⃣ Відкрийте браузер

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎉 Готово!

Система запущена і готова до використання!

---

Детальну документацію дивіться в [DOCKER_README.md](DOCKER_README.md)
