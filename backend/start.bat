@echo off
echo Starting EduAssistant Backend...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Start uvicorn server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
