@echo off
REM Quick start script for AI Agents Demo with Hugging Face on Windows

echo Starting AI Agents Demo with Hugging Face...
echo.

if not exist "backend\.env" (
    echo Error: backend\.env not found
    echo.
    echo Setup steps:
    echo 1. cd backend
    echo 2. copy .env.example .env
    echo 3. Get free token: https://huggingface.co/settings/tokens
    echo 4. Add HF_API_TOKEN=hf_... to backend\.env
    echo 5. Run this script again
    pause
    exit /b 1
)

echo Starting Python backend...
start "Backend" cmd /k "cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements_huggingface.txt && python main_huggingface.py"

timeout /t 3 /nobreak > nul

echo Starting React frontend...
start "Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo Everything is running!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Cost: $0.00 (using free Hugging Face)
echo Model: Llama 3.3 70B Instruct
echo Mode: Demanding orchestrator with critique loops
echo.
pause
