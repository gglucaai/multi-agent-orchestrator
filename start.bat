@echo off
REM Quick start script for AI Agents Demo on Windows

echo Starting AI Agents Demo...

if not exist "backend\.env" (
    echo Error: backend\.env not found
    echo Please copy backend\.env.example to backend\.env and add your API key
    pause
    exit /b 1
)

echo Starting Python backend...
start "Backend" cmd /k "cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python main.py"

timeout /t 3 /nobreak > nul

echo Starting React frontend...
start "Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo Both servers are starting!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Close the terminal windows to stop servers
pause
