#!/bin/bash
# Quick start script for AI Agents Demo with OLLAMA (Free, Local)

echo "🦙 Starting AI Agents Demo with Ollama..."
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Error: Ollama is not installed"
    echo "Install from: https://ollama.com"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running. Starting it now..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 3
fi

# Check if model is available
if ! ollama list | grep -q "llama3.1:8b"; then
    echo "📥 Model not found. Pulling llama3.1:8b (this may take a few minutes)..."
    ollama pull llama3.1:8b
fi

echo "✅ Ollama is ready"
echo ""

# Start backend
echo "📡 Starting Python backend (Ollama version)..."
cd backend
python -m venv venv 2>/dev/null
source venv/bin/activate
pip install -q -r requirements_ollama.txt
python main_ollama.py &
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
echo "💰 Cost: $0.00 (running locally with Ollama)"
echo ""
echo "Press Ctrl+C to stop everything"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
