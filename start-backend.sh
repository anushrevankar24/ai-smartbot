#!/bin/bash

# ERP AI Assistant - Backend Start Script

echo "Starting ERP AI Assistant Backend..."
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Virtual environment not detected."
    echo "Activating .venv..."
    source .venv/bin/activate
fi

# Kill any existing process on port 8000
echo "Checking for existing processes on port 8000..."
PORT_PID=$(lsof -ti:8000)

if [ ! -z "$PORT_PID" ]; then
    echo "Found existing process (PID: $PORT_PID) on port 8000"
    echo "Killing existing process..."
    kill -9 $PORT_PID 2>/dev/null
    sleep 1
    echo "Previous session terminated"
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "ERROR: .env file not found!"
    echo "Please create a .env file with your credentials."
    exit 1
fi

echo ""
echo "Starting FastAPI backend server..."
echo "   API available at: http://localhost:8000"
echo "   API docs at: http://localhost:8000/docs"
echo ""
echo "To stop the backend:"
echo "   - Press Ctrl+C in this terminal, OR"
echo "   - Run: ./stop.sh in another terminal"
echo ""
echo "----------------------------------------"
echo ""

# Start FastAPI with uvicorn
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

