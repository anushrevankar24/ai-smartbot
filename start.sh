#!/bin/bash

# ERP AI Assistant - Start Script
# This script cleans old processes and starts both backend and frontend

echo "=========================================="
echo "ERP AI Assistant - Starting Application"
echo "=========================================="
echo ""

# Get script directory for absolute paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Step 1: Clean up old processes
echo "Step 1: Cleaning up old processes..."
echo ""

# Find and kill process on port 8000 (Backend)
BACKEND_PID=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$BACKEND_PID" ]; then
    echo "   Found backend process (PID: $BACKEND_PID) on port 8000"
    kill -9 $BACKEND_PID 2>/dev/null
    sleep 1
    echo "   [OK] Backend process terminated"
else
    echo "   [OK] No backend process running on port 8000"
fi

# Find and kill process on port 8080 (Frontend)
FRONTEND_PID=$(lsof -ti:8080 2>/dev/null)
if [ ! -z "$FRONTEND_PID" ]; then
    echo "   Found frontend process (PID: $FRONTEND_PID) on port 8080"
    kill -9 $FRONTEND_PID 2>/dev/null
    sleep 1
    echo "   [OK] Frontend process terminated"
else
    echo "   [OK] No frontend process running on port 8080"
fi

# Also kill any uvicorn processes just to be safe
UVICORN_PIDS=$(pgrep -f "uvicorn api:app" 2>/dev/null)
if [ ! -z "$UVICORN_PIDS" ]; then
    echo "   Cleaning up remaining uvicorn processes..."
    echo "$UVICORN_PIDS" | xargs kill -9 2>/dev/null
    echo "   [OK] Uvicorn processes cleaned"
fi

# Also kill any vite processes just to be safe
VITE_PIDS=$(pgrep -f "vite" 2>/dev/null)
if [ ! -z "$VITE_PIDS" ]; then
    echo "   Cleaning up remaining vite processes..."
    echo "$VITE_PIDS" | xargs kill -9 2>/dev/null
    echo "   [OK] Vite processes cleaned"
fi

echo ""
echo "Step 2: Starting Backend..."
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "   Activating virtual environment..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo "   [OK] Virtual environment activated"
    else
        echo "   WARNING: .venv not found, assuming Python environment is ready"
    fi
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "   ERROR: .env file not found!"
    echo "   Please create a .env file with your credentials."
    exit 1
fi

# Start backend in background
echo "   Starting FastAPI backend server on port 8000..."
cd "$SCRIPT_DIR"
nohup uvicorn api:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_NEW_PID=$!
sleep 2

# Check if backend started successfully
if ps -p $BACKEND_NEW_PID > /dev/null 2>&1; then
    echo "   [OK] Backend started (PID: $BACKEND_NEW_PID)"
else
    echo "   ERROR: Backend failed to start. Check backend.log for details."
    exit 1
fi

echo ""
echo "Step 3: Starting Frontend..."
echo ""

# Navigate to frontend directory
if [ -d "$SCRIPT_DIR/chatbot-ui" ]; then
    cd "$SCRIPT_DIR/chatbot-ui" || exit 1
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "   Installing frontend dependencies..."
        npm install
        echo "   [OK] Dependencies installed"
    fi
    
    # Start frontend in background
    echo "   Starting React development server on port 8080..."
    nohup npm run dev > "$SCRIPT_DIR/frontend.log" 2>&1 &
    FRONTEND_NEW_PID=$!
    sleep 3
    
    # Check if frontend started successfully
    if ps -p $FRONTEND_NEW_PID > /dev/null 2>&1; then
        echo "   [OK] Frontend started (PID: $FRONTEND_NEW_PID)"
    else
        echo "   WARNING: Frontend may still be starting. Check frontend.log for details."
    fi
else
    echo "   ERROR: chatbot-ui directory not found!"
    exit 1
fi

echo ""
echo "=========================================="
echo "SUCCESS: Application Started Successfully!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Backend API:  http://localhost:8000"
echo "  - API Docs:     http://localhost:8000/docs"
echo "  - Frontend UI:  http://localhost:8080"
echo ""
echo "Logs:"
echo "  - Backend:  tail -f backend.log"
echo "  - Frontend: tail -f frontend.log"
echo ""
echo "To stop all services:"
echo "  ./stop.sh"
echo ""
echo "=========================================="

