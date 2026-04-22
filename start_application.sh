#!/bin/bash
set -e

cd /Users/luli/Desktop/OpenSourceProjects/DocumentsAnalysis

echo "Starting Document Q&A Application..."
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv_test" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Load backend env file if available so runtime matches test config.
if [ -f "backend/.env" ]; then
    set -a
    source "backend/.env"
    set +a
fi

# Fall back only if values are still missing.
export KIMI_API_KEY="${KIMI_API_KEY:-your_api_key_here}"
export KIMI_BASE_URL="${KIMI_BASE_URL:-https://api.moonshot.cn/v1}"

echo "🔧 Environment configured:"
echo "  - KIMI_API_KEY: ${KIMI_API_KEY:0:10}..."
echo "  - KIMI_BASE_URL: $KIMI_BASE_URL"
echo ""

# Start Backend
echo "🚀 Starting Backend Server..."
cd backend
../venv_test/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
cd ..
BACKEND_PID=$!

echo "  Backend PID: $BACKEND_PID"
echo "  API URL: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""

# Wait for backend to start
sleep 3

# Start Frontend
echo "🚀 Starting Frontend Server..."
cd frontend
npm run dev &
cd ..
FRONTEND_PID=$!

echo "  Frontend PID: $FRONTEND_PID"
echo "  Web UI: http://localhost:5173"
echo ""

# Check if services are running
sleep 2
echo "🔍 Checking service status..."

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✅ Backend: Running"
else
    echo "  ⚠️  Backend: Starting... (may take a moment)"
fi

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "  ✅ Frontend: Running"
else
    echo "  ⚠️  Frontend: Starting... (may take a moment)"
fi

echo ""
echo "===================================="
echo "✨ Application Started Successfully!"
echo ""
echo "📱 Access Points:"
echo "   • Web UI:       http://localhost:5173"
echo "   • API:          http://localhost:8000"
echo "   • API Docs:     http://localhost:8000/docs"
echo ""
echo "⚠️  Note: Make sure to set your KIMI_API_KEY in backend/.env"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "===================================="

# Keep script running
wait
