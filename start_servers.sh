#!/bin/bash
cd /Users/luli/Desktop/OpenSourceProjects/DocumentsAnalysis

# Start Backend
cd backend
../venv_test/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
echo "Backend started on http://localhost:8000"
cd ..

# Start Frontend
cd frontend
npm run dev &
echo "Frontend started on http://localhost:5173"

echo ""
echo "Both servers are starting up..."
echo "- API Docs: http://localhost:8000/docs"
echo "- Web UI: http://localhost:5173"
