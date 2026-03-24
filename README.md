# 📚 EduAssistant - Система валідації та генерації навчальних матеріалів

Система для валідації курсових робіт на відповідність нормативним документам та автоматичної генерації навчальних матеріалів.

## ✨ Можливості

### 🔍 Валідація документів
- Перевірка курсових робіт на відповідність ДСТУ та іншим стандартам
- Детальні звіти з виявленими проблемами
- Рекомендації щодо виправлення

### 📝 Генерація матеріалів
- **Конспекти**: Детальні, структуровані конспекти з документів
- **Тести**: Автоматична генерація тестових питань
- **Флеш-картки**: Картки для запам'ятовування термінів
- **Глосарії**: Словники ключових термінів

### 💬 AI Чат
- Інтелектуальний чат з документами
- Відповіді на основі змісту завантажених файлів
- Контекстне розуміння питань

### 📄 Експорт
- Завантаження матеріалів у форматі .docx
- Правильне форматування (Times New Roman 14pt)
- Вирівнювання тексту по ширині

## 🏗️ Технології

### Backend
- **FastAPI** - веб-фреймворк
- **Python 3.11** - мова програмування
- **Supabase** - база даних (PostgreSQL)
- **Qdrant** - векторна база для RAG
- **Groq** - LLM для генерації (llama-3.1-8b-instant)
- **Sentence Transformers** - embeddings
- **python-docx** - робота з документами

### Frontend
- **React** - UI фреймворк
- **Vite** - build tool
- **Axios** - HTTP клієнт
- **React Router** - маршрутизація

### Infrastructure
- **Docker** & **Docker Compose** - контейнеризація
- **Nginx** - веб-сервер для frontend

## 🚀 Швидкий старт

### За допомогою Docker (рекомендовано)

1. **Клонуйте репозиторій:**
```bash
git clone https://github.com/yourusername/coursework_1.git
cd coursework_1
```

2. **Налаштуйте змінні оточення:**
```bash
# Windows
copy .env.example .env
copy backend\.env.example backend\.env

# Linux/Mac
cp .env.example .env
cp backend/.env.example backend/.env
```

3. **Відредагуйте `backend/.env`** і додайте свої ключі:
   - Supabase credentials
   - Groq API key
   - Qdrant credentials

4. **Запустіть проект:**
```bash
# Windows
start.bat

# Linux/Mac
./start.sh

# Або вручну
docker-compose up --build
```

5. **Відкрийте в браузері:**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Локальний запуск (без Docker)

<details>
<summary>Розгорнути інструкцію</summary>

#### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

</details>

## 📁 Структура проекту

```
coursework_1/
├── backend/                    # Backend FastAPI
│   ├── main.py                # Головний файл
│   ├── auth.py                # Аутентифікація
│   ├── config.py              # Конфігурація
│   ├── document_parser.py     # Парсинг документів
│   ├── validators.py          # Валідація
│   ├── generators.py          # Генерація матеріалів
│   ├── rag_engine.py          # RAG система
│   ├── docx_exporter.py       # Експорт в DOCX
│   ├── requirements.txt       # Python залежності
│   └── Dockerfile             # Docker image
│
├── frontend/                   # Frontend React
│   ├── src/
│   │   ├── components/        # React компоненти
│   │   ├── pages/             # Сторінки
│   │   ├── api/               # API клієнт
│   │   └── contexts/          # React контексти
│   ├── package.json           # Node залежності
│   ├── Dockerfile             # Docker image
│   └── nginx.conf             # Nginx конфігурація
│
├── docker-compose.yml          # Docker Compose
├── .env.example               # Приклад env
├── start.bat                  # Запуск Windows
├── start.sh                   # Запуск Linux/Mac
├── QUICKSTART.md              # Швидкий старт
└── DOCKER_README.md           # Docker документація
```

## 🔑 Необхідні сервіси

Перед запуском потрібно налаштувати:

1. **Supabase** (https://supabase.com)
   - Створіть проект
   - Скопіюйте URL і API keys
   - Виконайте міграції з `backend/migration_*.sql`

2. **Groq** (https://console.groq.com)
   - Зареєструйтесь
   - Створіть API key

3. **Qdrant** (https://qdrant.tech)
   - Створіть кластер (або використайте локально)
   - Скопіюйте URL і API key

## 📝 API Документація

Після запуску backend доступна інтерактивна документація:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Внесок

Pull requests вітаються! Для великих змін спочатку відкрийте issue для обговорення.

## 📄 Ліцензія

[MIT](LICENSE)

## 👨‍💻 Автор

Ваше ім'я - [@yourusername](https://github.com/yourusername)

## 🙏 Подяки

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Supabase](https://supabase.com/)
- [Groq](https://groq.com/)
- [Qdrant](https://qdrant.tech/)
