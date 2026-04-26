"""Тестування підключення до всіх сервісів"""
import os
import sys
from dotenv import load_dotenv

# Встановлюємо UTF-8 для Windows консолі
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def test_groq():
    """Тест Groq API"""
    print("\n" + "="*50)
    print("🤖 GROQ API")
    print("="*50)
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Простий тестовий запит
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'OK' if you work"}],
            max_tokens=10
        )

        answer = response.choices[0].message.content
        print(f"✅ З'єднання успішне!")
        print(f"📝 Відповідь: {answer}")
        print(f"🔑 API Key: {os.getenv('GROQ_API_KEY')[:20]}...")
        return True
    except Exception as e:
        print(f"❌ Помилка: {e}")
        print(f"🔑 API Key: {os.getenv('GROQ_API_KEY')}")
        return False


def test_supabase():
    """Тест Supabase"""
    print("\n" + "="*50)
    print("🗄️  SUPABASE DATABASE")
    print("="*50)
    try:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        print(f"📍 URL: {url}")
        print(f"🔑 Key: {key[:20]}...")

        client = create_client(url, key)

        # Пробуємо запит до БД
        result = client.table("documents").select("id").limit(1).execute()

        print(f"✅ З'єднання успішне!")
        print(f"📊 Знайдено документів: {len(result.data)}")
        return True
    except Exception as e:
        print(f"❌ Помилка: {e}")
        error_str = str(e)
        if "getaddrinfo failed" in error_str:
            print("🔴 DNS помилка: Supabase проєкт не існує або URL неправильний")
        elif "Invalid API key" in error_str:
            print("🔴 Невірний API ключ")
        return False


def test_qdrant():
    """Тест Qdrant"""
    print("\n" + "="*50)
    print("🔍 QDRANT VECTOR DB")
    print("="*50)
    try:
        from qdrant_client import QdrantClient

        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")

        print(f"📍 URL: {url}")
        print(f"🔑 API Key: {api_key[:20]}...")

        client = QdrantClient(url=url, api_key=api_key)

        # Отримуємо список колекцій
        collections = client.get_collections()

        print(f"✅ З'єднання успішне!")
        print(f"📦 Колекції: {[c.name for c in collections.collections]}")

        # Перевіряємо нашу колекцію
        if collections.collections:
            for col in collections.collections:
                if col.name == "edu_docs":
                    info = client.get_collection("edu_docs")
                    print(f"📊 Векторів у 'edu_docs': {info.points_count}")

        return True
    except Exception as e:
        print(f"❌ Помилка: {e}")
        return False


def test_huggingface():
    """Тест HuggingFace Token"""
    print("\n" + "="*50)
    print("🤗 HUGGINGFACE")
    print("="*50)
    try:
        token = os.getenv("HF_TOKEN")

        if not token:
            print("⚠️  HF_TOKEN не встановлено")
            return False

        print(f"🔑 Token: {token[:20]}...")

        # Простий запит до HF API
        import requests
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://huggingface.co/api/whoami",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ З'єднання успішне!")
            print(f"👤 User: {data.get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Помилка: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Помилка: {e}")
        return False


def main():
    """Запуск всіх тестів"""
    print("\n" + "🔬 ТЕСТУВАННЯ ПІДКЛЮЧЕННЯ ДО СЕРВІСІВ")
    print("="*50)

    results = {
        "Groq": test_groq(),
        "Supabase": test_supabase(),
        "Qdrant": test_qdrant(),
        "HuggingFace": test_huggingface(),
    }

    print("\n" + "="*50)
    print("📊 ПІДСУМОК")
    print("="*50)

    for service, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {service}: {'OK' if status else 'FAILED'}")

    total = len(results)
    success = sum(results.values())
    print(f"\n🎯 Успішно: {success}/{total}")

    if success == total:
        print("✅ Всі сервіси працюють!")
    else:
        print("⚠️  Є проблеми з підключенням")


if __name__ == "__main__":
    main()
