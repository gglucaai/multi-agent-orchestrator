@echo off
REM Quick start script for AI Agents Demo with OLLAMA (Free, Local) on Windows

echo Starting AI Agents Demo with Ollama...
echo.

REM Check if Ollama is installed
where ollama >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Ollama is not installed
    echo Install from: https://ollama.com
    pause
    exit /b 1
)

echo Checking Ollama status...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Starting Ollama...
    start "Ollama" cmd /k "ollama serve"
    timeout /t 3 /nobreak > nul
)

REM Check if model exists
ollama list | findstr "llama3.1:8b" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Pulling llama3.1:8b model...
    ollama pull llama3.1:8b
)

echo Ollama is ready
echo.

echo Starting Python backend...
start "Backend" cmd /k "cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements_ollama.txt && python main_ollama.py"

timeout /t 3 /nobreak > nul

echo Starting React frontend...
start "Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo Everything is running!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Cost: $0.00 (running locally with Ollama)
echo.
echo Close the terminal windows to stop servers
pause
