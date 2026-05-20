#!/bin/bash
# Quick start script for AI Agents Demo with Hugging Face

echo "🤗 Starting AI Agents Demo with Hugging Face..."
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env not found"
    echo ""
    echo "Setup steps:"
    echo "1. cd backend && cp .env.example .env"
    echo "2. Get free token: https://huggingface.co/settings/tokens"
    echo "3. Add HF_API_TOKEN=hf_... to backend/.env"
    echo "4. Run this script again"
    exit 1
fi

# Check token
if ! grep -q "HF_API_TOKEN=hf_" backend/.env; then
    echo "⚠️  HF_API_TOKEN not configured properly in backend/.env"
    echo "Get token from: https://huggingface.co/settings/tokens"
    exit 1
fi

# Start backend
echo "📡 Starting Python backend (Hugging Face version)..."
cd backend
python -m venv venv 2>/dev/null
source venv/bin/activate
pip install -q -r requirements_huggingface.txt
python main_huggingface.py &
BACKEND_PID=$!
cd ..

sleep 3

# Start frontend
echo "🎨 Starting React frontend..."
cd frontend
npm install --silent
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Everything is running!"
echo "📍 Backend: http://localhost:8000"
echo "📍 Frontend: http://localhost:3000"
echo ""
echo "💰 Cost: \$0.00 (using free Hugging Face Inference API)"
echo "🤖 Model: Llama 3.3 70B Instruct"
echo "💬 Mode: Demanding orchestrator with critique loops"
echo ""
echo "Press Ctrl+C to stop everything"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
