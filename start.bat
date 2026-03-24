@echo off
echo ===================================
echo   Coursework Docker Launcher
echo ===================================
echo.

REM Перевірка чи існує .env файл
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please copy .env.example to .env and fill in your credentials
    echo.
    echo Run: copy .env.example .env
    pause
    exit /b 1
)

if not exist "backend\.env" (
    echo [ERROR] backend/.env file not found!
    echo Please copy backend/.env.example to backend/.env and fill in your credentials
    echo.
    echo Run: copy backend\.env.example backend\.env
    pause
    exit /b 1
)

echo [INFO] Environment files found!
echo.
echo [INFO] Starting Docker containers...
echo.

docker-compose up --build

pause
