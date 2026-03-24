import os
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client
from qdrant_client import QdrantClient

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Звичайний клієнт (для операцій з RLS - Row Level Security)
# Використовує anon key, працює з auth токенами користувачів
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Admin клієнт (для операцій БЕЗ RLS)
# Використовує service_role key, має повний доступ
# ВАЖЛИВО: використовувати тільки на бекенді, НІКОЛИ не передавати на фронтенд!
supabase_admin = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")  # Service role key з Settings -> API
)


def get_user_supabase(access_token: str) -> Client:
    """
    Створює Supabase клієнт з JWT токеном користувача для RLS

    Args:
        access_token: JWT токен від Supabase Auth

    Returns:
        Supabase client з встановленим токеном користувача
    """
    client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    # Встановлюємо токен для RLS
    client.postgrest.auth(access_token)
    return client

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)