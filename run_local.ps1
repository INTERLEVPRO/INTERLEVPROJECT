# INTERLEV Agentic AI Local Run Script
# This script starts the backend and worker using local Python (no Docker/Redis required)

$PYTHON_PATH = "C:\Users\PC\CU-WITH-CODE\.runtime\python312\python.exe"

# 1. Start FastAPI Backend
Write-Host "🚀 Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Cyan
Start-Process -FilePath $PYTHON_PATH -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000" -NoNewWindow

# 2. Start Celery Worker (Filesystem Mode)
Write-Host "🤖 Starting Celery Worker (using filesystem broker)..." -ForegroundColor Green
Start-Process -FilePath $PYTHON_PATH -ArgumentList "-m celery -A backend.app.tasks.celery_app worker --loglevel=info --pool=solo -Q agent_queue" -NoNewWindow

Write-Host "✅ All systems started! You can now use the API at http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Note: Frontend dashboard requires Node.js/Docker. Using local Python for backend only."
