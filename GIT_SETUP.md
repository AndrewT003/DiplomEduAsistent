# 📦 Git Setup Guide

Інструкція по налаштуванню Git репозиторію та першому commit.

## 🎯 Один репозиторій (Monorepo)

Ваш проект використовує **monorepo** структуру - один репозиторій для backend і frontend.

## 🚀 Перший commit

### 1. Перевірте що .gitignore налаштовано

`.gitignore` вже створено і містить:
- `.env` файли (щоб не виставити ключі публічно)
- `node_modules/` та `__pycache__/`
- IDE файли
- Тимчасові файли

### 2. Ініціалізуйте Git (якщо ще не зроблено)

```bash
cd C:\Users\kaktu\Desktop\coursework_1
git init
```

### 3. Додайте всі файли

```bash
git add .
```

### 4. Перевірте що буде закоммічено

```bash
git status
```

**Важливо!** Переконайтеся що `.env` файли **НЕ** в списку:
- ❌ `backend/.env` - НЕ має бути
- ✅ `backend/.env.example` - має бути
- ❌ `.env` - НЕ має бути
- ✅ `.env.example` - має бути

### 5. Створіть перший commit

```bash
git commit -m "Initial commit: EduAssistant project with Docker support"
```

### 6. Створіть репозиторій на GitHub

1. Йдіть на https://github.com/new
2. Назва: `coursework-eduassistant` (або інша)
3. Description: "Система валідації та генерації навчальних матеріалів"
4. **НЕ** додавайте README, .gitignore, license (у вас вже є)
5. Натисніть "Create repository"

### 7. Додайте remote і запуште

GitHub покаже команди, але ось приклад:

```bash
# Додайте remote
git remote add origin https://github.com/ВАШЕ_ІМЯ/coursework-eduassistant.git

# Перейменуйте гілку на main (якщо потрібно)
git branch -M main

# Запуште код
git push -u origin main
```

## 📝 Наступні commits

Після змін в коді:

```bash
# Перегляньте зміни
git status

# Додайте змінені файли
git add .

# Або додайте конкретні файли
git add backend/main.py frontend/src/App.jsx

# Створіть commit з описом
git commit -m "Add feature: описання фічі"

# Запуште на GitHub
git push
```

## 🌿 Робота з гілками (опціонально)

Для великих змін краще створювати окремі гілки:

```bash
# Створіть нову гілку
git checkout -b feature/new-feature

# Працюйте над фічею...
git add .
git commit -m "Add new feature"

# Запуште гілку на GitHub
git push -u origin feature/new-feature

# Після цього створіть Pull Request на GitHub
```

## 🔒 Безпека

### ⚠️ КРИТИЧНО ВАЖЛИВО:

**НІКОЛИ не коммітьте:**
- `.env` файли з реальними ключами
- API keys, паролі, токени
- Приватні дані користувачів

### Що робити якщо випадково закоммітили .env:

```bash
# Видаліть файл з git (але залиште локально)
git rm --cached backend/.env

# Додайте в .gitignore якщо ще не додано
echo "backend/.env" >> .gitignore

# Закоммітьте зміни
git add .gitignore
git commit -m "Remove .env from tracking"
git push

# ВАЖЛИВО: Змініть всі ключі які були в .env!
```

## 📊 Рекомендовані commit messages

Використовуйте чіткі описи:

```bash
# Добре ✅
git commit -m "Add user authentication with JWT"
git commit -m "Fix: markdown symbols in document export"
git commit -m "Update: improve AI prompt for better summaries"

# Погано ❌
git commit -m "fix"
git commit -m "update"
git commit -m "changes"
```

## 🏷️ Git tags для версій (опціонально)

```bash
# Створіть tag для версії
git tag -a v1.0.0 -m "Version 1.0.0: Initial release"

# Запуште tags
git push --tags
```

## 📦 Корисні команди

```bash
# Перегляд історії
git log --oneline

# Скасування незбережених змін
git checkout -- файл.py

# Перегляд різниці
git diff

# Перегляд віддалених репозиторіїв
git remote -v

# Отримати останні зміни з GitHub
git pull

# Клонувати репозиторій (для інших)
git clone https://github.com/ВАШЕ_ІМЯ/coursework-eduassistant.git
```

## ✅ Checklist перед першим push

- [ ] `.env` файли додані в `.gitignore`
- [ ] Перевірено `git status` - немає приватних даних
- [ ] README.md заповнено
- [ ] .env.example файли створені з прикладами
- [ ] Dockerfile та docker-compose.yml протестовані
- [ ] Все працює локально

## 🎉 Готово!

Ваш проект тепер на GitHub і готовий до роботи!

Посилання на репозиторій: `https://github.com/ВАШЕ_ІМЯ/НАЗВА_РЕПО`
