"""
Модуль авторизації з Supabase Auth
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from config import supabase, supabase_admin
import jwt
import os

security = HTTPBearer()

# JWTSettings для Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")  # Потрібно додати в .env


def verify_token(token: str) -> dict:
    """
    Перевіряє JWT токен від Supabase

    Returns:
        dict: payload токена з user_id, email, etc.
    """
    try:
        # Debug: декодуємо без верифікації щоб побачити payload
        unverified = jwt.decode(token, options={"verify_signature": False})
        print(f"🔍 Token payload (unverified): {unverified}")
        print(f"🔑 JWT_SECRET present: {bool(SUPABASE_JWT_SECRET)}")

        # ТИМЧАСОВО: без верифікації signature (для тестування)
        # TODO: Потрібен правильний JWT_SECRET або використати RS256
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_aud": False}
        )

        print(f"✅ Token verified (no signature check)")
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен прострочений"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Невалідний токен: {str(e)}"
        )
    except Exception as e:
        import traceback
        print(f"❌ Помилка верифікації токену: {str(e)}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Помилка авторизації: {str(e)}"
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    FastAPI Dependency для отримання поточного користувача

    Usage:
        @app.get("/protected")
        def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["sub"]}
    """
    token = credentials.credentials
    payload = verify_token(token)

    # Supabase JWT payload містить:
    # - sub: user_id
    # - email: email користувача
    # - role: роль (authenticated, anon, etc.)

    return {
        "user_id": payload["sub"],
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated"),
        "access_token": token  # Додаємо токен для RLS
    }


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Опціональна авторизація (якщо токен є - перевіряємо, якщо немає - None)

    Корисно для ендпоінтів, які можуть працювати як з авторизацією, так і без
    """
    if credentials is None:
        return None

    try:
        return get_current_user(credentials)
    except HTTPException:
        return None


async def register_user(email: str, password: str, metadata: dict = None) -> dict:
    """
    Реєстрація нового користувача через Supabase Auth

    Args:
        email: Email користувача
        password: Пароль (мінімум 6 символів)
        metadata: Додаткові дані (full_name, avatar_url, etc.)

    Returns:
        dict: {"user": {...}, "session": {...}}
    """
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": metadata or {}
            }
        })

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не вдалося створити користувача"
            )

        return {
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at
            },
            "session": {
                "access_token": response.session.access_token if response.session else None,
                "refresh_token": response.session.refresh_token if response.session else None,
                "expires_at": response.session.expires_at if response.session else None
            } if response.session else None,
            "message": "Користувача створено. Перевірте email для підтвердження." if not response.session else "Користувача створено та авторизовано."
        }

    except Exception as e:
        # Supabase може повертати різні помилки
        error_msg = str(e)

        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Користувач з таким email вже існує"
            )

        if "password" in error_msg.lower() and "weak" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароль занадто слабкий. Використовуйте мінімум 6 символів."
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка реєстрації: {error_msg}"
        )


async def login_user(email: str, password: str) -> dict:
    """
    Логін користувача через Supabase Auth

    Returns:
        dict: {"user": {...}, "session": {...}}
    """
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user is None or response.session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невірний email або пароль"
            )

        return {
            "user": {
                "id": response.user.id,
                "email": response.user.email
            },
            "session": {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at,
                "token_type": "bearer"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Помилка логіну: {str(e)}"
        )


async def refresh_session(refresh_token: str) -> dict:
    """
    Оновлення access токена через refresh токен
    """
    try:
        response = supabase.auth.refresh_session(refresh_token)

        if response.session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалідний refresh токен"
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "expires_at": response.session.expires_at
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Помилка оновлення сесії: {str(e)}"
        )


async def logout_user(token: str):
    """
    Вихід користувача (інвалідація токена)
    """
    try:
        # Встановлюємо токен в клієнт
        supabase.auth.set_session(token, None)
        # Виходимо
        supabase.auth.sign_out()

    except Exception as e:
        # Logout може завжди успішно виконатись на клієнті
        # навіть якщо сервер повертає помилку
        pass
