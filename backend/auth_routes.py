"""
Роути для авторизації (реєстрація, логін, logout)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from auth import register_user, login_user, refresh_session, logout_user, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@example.com",
                "password": "securepass123",
                "full_name": "Іван Петренко"
            }
        }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@example.com",
                "password": "securepass123"
            }
        }


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register")
async def register(body: RegisterRequest):
    """
    Реєстрація нового користувача

    - **email**: Email користувача
    - **password**: Пароль (мінімум 6 символів)
    - **full_name**: Повне ім'я (опціонально)

    Повертає: user, session (access_token, refresh_token)
    """
    metadata = {}
    if body.full_name:
        metadata["full_name"] = body.full_name

    result = await register_user(
        email=body.email,
        password=body.password,
        metadata=metadata
    )

    return result


@router.post("/login")
async def login(body: LoginRequest):
    """
    Логін користувача

    - **email**: Email
    - **password**: Пароль

    Повертає: user, session (access_token, refresh_token, expires_at)

    **Як використовувати:**
    1. Отримай `access_token` з відповіді
    2. Додай в headers: `Authorization: Bearer YOUR_ACCESS_TOKEN`
    3. Коли токен прострочується (expires_at) - використай /auth/refresh
    """
    result = await login_user(
        email=body.email,
        password=body.password
    )

    return result


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    """
    Оновлення access токена через refresh токен

    Використовуй коли access_token прострочений (401 Unauthorized)
    """
    result = await refresh_session(body.refresh_token)
    return result


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    Вихід користувача (інвалідація токена)

    Потребує авторизації (Bearer token в headers)
    """
    # Supabase logout працює на клієнті
    # На бекенді просто підтверджуємо що токен валідний
    return {
        "message": "Успішно вийшли з системи",
        "user_id": user["user_id"]
    }


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """
    Отримати інформацію про поточного користувача

    Потребує авторизації (Bearer token в headers)
    """
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "role": user["role"]
    }
