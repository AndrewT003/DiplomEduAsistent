# PowerShell startup script for EduAssistant Backend

Write-Host "Starting EduAssistant Backend..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Start uvicorn server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
