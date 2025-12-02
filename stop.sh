#!/bin/bash

# ERP AI Assistant - Stop Script

echo "Stopping ERP AI Assistant..."
echo ""

# Find and kill process on port 8000 (Backend)
BACKEND_PID=$(lsof -ti:8000)
if [ ! -z "$BACKEND_PID" ]; then
    echo "   Found backend process (PID: $BACKEND_PID) on port 8000"
    kill -9 $BACKEND_PID 2>/dev/null
    sleep 1
    echo "   Backend stopped successfully"
else
    echo "   No backend process running on port 8000"
fi

# Find and kill process on port 8080 (Frontend)
FRONTEND_PID=$(lsof -ti:8080)
if [ ! -z "$FRONTEND_PID" ]; then
    echo "   Found frontend process (PID: $FRONTEND_PID) on port 8080"
    kill -9 $FRONTEND_PID 2>/dev/null
    sleep 1
    echo "   Frontend stopped successfully"
else
    echo "   No frontend process running on port 8080"
fi

# Also kill any uvicorn processes just to be safe
UVICORN_PIDS=$(pgrep -f "uvicorn api:app")
if [ ! -z "$UVICORN_PIDS" ]; then
    echo "   Cleaning up remaining uvicorn processes..."
    echo "$UVICORN_PIDS" | xargs kill -9 2>/dev/null
fi

# Also kill any vite processes just to be safe
VITE_PIDS=$(pgrep -f "vite")
if [ ! -z "$VITE_PIDS" ]; then
    echo "   Cleaning up remaining vite processes..."
    echo "$VITE_PIDS" | xargs kill -9 2>/dev/null
fi

echo ""
echo "All done!"

