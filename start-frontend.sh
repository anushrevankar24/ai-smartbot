#!/bin/bash

# ERP AI Assistant - Frontend Start Script

echo "Starting ERP AI Assistant Frontend..."
echo ""

# Check if we're in the chatbot-ui directory
if [ ! -f "package.json" ]; then
    echo "Changing to chatbot-ui directory..."
    cd chatbot-ui || exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "node_modules not found. Installing dependencies..."
    npm install
fi

echo ""
echo "Starting React development server..."
echo "   Frontend available at: http://localhost:8080"
echo ""
echo "To stop the frontend:"
echo "   - Press Ctrl+C in this terminal"
echo ""
echo "----------------------------------------"
echo ""

# Start React dev server
npm run dev

