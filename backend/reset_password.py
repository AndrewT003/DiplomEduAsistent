"""Скрипт для скидання паролю користувача"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from config import supabase_admin

# Email користувача
USER_EMAIL = "timcenkoandrij84@gmail.com"

# Новий пароль (мінімум 6 символів)
NEW_PASSWORD = "Test123456"  # ЗМІНІТЬ ЦЕЙ ПАРОЛЬ!

try:
    # Оновлюємо пароль через Admin API
    response = supabase_admin.auth.admin.update_user_by_id(
        uid="7c8c7581-be62-4b00-b217-862d1f0101df",
        attributes={"password": NEW_PASSWORD}
    )

    print("✅ Пароль успішно оновлено!")
    print(f"📧 Email: {USER_EMAIL}")
    print(f"🔑 Новий пароль: {NEW_PASSWORD}")
    print("\n⚠️  ВАЖЛИВО: Змініть пароль після входу!")

except Exception as e:
    print(f"❌ Помилка: {e}")
